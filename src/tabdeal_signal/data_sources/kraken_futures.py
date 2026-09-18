"""Read-only Kraken Futures public chart adapter."""
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from json import loads

from .contracts import DataProvenance, DataQualityStatus, DataSnapshotMetadata, NormalizedSnapshot, ReadOnlyDataSource, SourceKind

_RESOLUTIONS = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60, "4h": 240, "12h": 720, "1d": 1440, "1w": 10080}
_TICK_TYPES = {"spot", "mark", "trade"}


class KrakenFuturesPublicCandleDataSource(ReadOnlyDataSource):
    """Fetch one public Kraken Futures chart-candle response."""

    _PROVENANCE = DataProvenance(
        source="kraken-futures-public-charts",
        reference="https://docs.kraken.com/api/docs/futures-api/charts/candles",
        schema_version="kraken-futures-report-003",
    )

    def __init__(self, tick_type: str, symbol: str, resolution: str, *, timeout_seconds: float = 5.0, transport=None, base_url: str = "https://futures.kraken.com") -> None:
        tick_type, symbol, resolution = tick_type.strip().lower(), symbol.strip(), resolution.strip()
        if tick_type not in _TICK_TYPES:
            raise ValueError("unsupported Kraken Futures tick type")
        if not symbol:
            raise ValueError("symbol must be non-empty")
        if resolution not in _RESOLUTIONS:
            raise ValueError("unsupported Kraken Futures chart resolution")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if not isinstance(base_url, str) or not base_url.startswith("https://"):
            raise ValueError("base_url must be HTTPS")
        self.tick_type, self.symbol, self.resolution = tick_type, symbol, resolution
        self.timeout_seconds, self.base_url = timeout_seconds, base_url.rstrip("/")
        self._transport = transport or _UrllibJsonTransport()

    def fetch_snapshot(self, *, as_of: datetime | None = None) -> NormalizedSnapshot:
        if as_of is not None:
            if as_of.tzinfo is None or as_of.utcoffset() is None:
                raise ValueError("as_of must be timezone-aware")
            as_of = as_of.astimezone(timezone.utc)
        url = f"{self.base_url}/api/charts/v1/{quote(self.tick_type, safe='')}/{quote(self.symbol, safe='')}/{quote(self.resolution, safe='')}"
        topic = f"kraken-futures-candles:{self.tick_type}:{self.symbol}:{self.resolution}"
        try:
            payload, received_at = self._transport.get(url, {}, self.timeout_seconds)
            if received_at.tzinfo is None or received_at.utcoffset() is None:
                raise ValueError("transport received_at must be timezone-aware")
            received_at = received_at.astimezone(timezone.utc)
        except HTTPError as exc:
            return self._failure(topic, datetime.now(timezone.utc), "rate_limited" if exc.code in (403, 429) else "http_error", str(exc.code))
        except (TimeoutError, URLError, OSError) as exc:
            return self._failure(topic, datetime.now(timezone.utc), "transport_error", type(exc).__name__)
        except ValueError as exc:
            return self._failure(topic, datetime.now(timezone.utc), "invalid_payload", str(exc))
        if as_of is not None and received_at > as_of:
            return self._failure(topic, received_at, "pit_unavailable", "received_after_as_of")
        if not isinstance(payload, Mapping):
            return self._failure(topic, received_at, "schema_error", "expected_object_response")
        candles = payload.get("candles")
        if candles is None:
            candles = payload.get("data")
        if not isinstance(candles, list):
            return self._failure(topic, received_at, "schema_error", "missing_candles_list")
        if not candles:
            return self._failure(topic, received_at, "pit_unavailable", "no_candles")
        try:
            normalized = tuple(self._normalize_row(row, as_of) for row in candles)
        except _PITUnavailable as exc:
            return self._failure(topic, received_at, "pit_unavailable", str(exc))
        except ValueError as exc:
            return self._failure(topic, received_at, "schema_error", str(exc))
        return NormalizedSnapshot(
            DataSnapshotMetadata(SourceKind.EXCHANGE, topic, received_at, available_at=received_at, quality=DataQualityStatus.VALID, provenance=self._PROVENANCE),
            {"tick_type": self.tick_type, "symbol": self.symbol, "resolution": self.resolution, "rows": normalized, "more_candles": payload.get("more_candles")},
        )

    def _normalize_row(self, row: object, as_of: datetime | None) -> object:
        if isinstance(row, Mapping):
            timestamp = row.get("time", row.get("timestamp"))
        elif isinstance(row, (list, tuple)) and row:
            timestamp = row[0]
        else:
            raise ValueError("unsupported candle row")
        try:
            numeric_timestamp = int(str(timestamp))
        except (TypeError, ValueError) as exc:
            raise ValueError("candle timestamp must be integer-like") from exc
        timestamp_ms = numeric_timestamp if numeric_timestamp >= 100_000_000_000 else numeric_timestamp * 1000
        opened_at = datetime.fromtimestamp(timestamp_ms / 1000, timezone.utc)
        if as_of is not None:
            closed_at = opened_at + timedelta(minutes=_RESOLUTIONS[self.resolution])
            if closed_at >= as_of:
                raise _PITUnavailable("candle close is not strictly before as_of")
        return row

    def _failure(self, topic: str, received_at: datetime, error_class: str, *detail: str) -> NormalizedSnapshot:
        quality = DataQualityStatus.INVALID if error_class in {"invalid_payload", "schema_error"} else DataQualityStatus.UNAVAILABLE
        return NormalizedSnapshot(DataSnapshotMetadata(SourceKind.EXCHANGE, topic, received_at, available_at=received_at, quality=quality, provenance=self._PROVENANCE), {"tick_type": self.tick_type, "symbol": self.symbol, "resolution": self.resolution, "error_class": error_class, "error_detail": "|".join(detail)})


class _UrllibJsonTransport:
    def get(self, url, params, timeout_seconds):
        request = Request(url, headers={"Accept": "application/json"}, method="GET")
        with urlopen(request, timeout=timeout_seconds) as response:
            return loads(response.read().decode("utf-8")), datetime.now(timezone.utc)


class _PITUnavailable(ValueError):
    pass


__all__ = ["KrakenFuturesPublicCandleDataSource"]
