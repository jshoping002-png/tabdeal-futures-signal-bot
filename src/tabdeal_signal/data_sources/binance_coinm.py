"""Read-only Binance Coin-M continuous-contract kline adapter.

The adapter preserves the documented continuous-kline rows instead of
inventing a project-specific candle schema. It enforces the report-level
request boundary, UTC PIT receipt semantics, and closed-candle filtering using
the documented kline row timestamps.
"""
from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler

from .contracts import (
    DataProvenance,
    DataQualityStatus,
    DataSnapshotMetadata,
    NormalizedSnapshot,
    ReadOnlyDataSource,
    SourceKind,
)

_ENDPOINT = "/dapi/v1/continuousKlines"
_CONTRACT_TYPES = {"PERPETUAL", "CURRENT_MONTH", "NEXT_MONTH", "CURRENT_QUARTER", "NEXT_QUARTER"}
# Report 001 documents a maximum limit of 1500 for this endpoint.
_LIMIT_MAX = 1500
_MAX_SPAN_DAYS = 200


class _NoRedirectHandler(HTTPRedirectHandler):
    """Reject redirects so the configured Binance host remains authoritative."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class BinanceCoinMContinuousKlineDataSource(ReadOnlyDataSource):
    """Fetch public Coin-M continuous contract klines without credentials."""

    _PROVENANCE = DataProvenance(
        source="binance-coinm-public-continuous-klines",
        reference="https://developers.binance.com/docs/derivatives/coin-margined-futures/market-data/Continuous-Contract-Kline-Candlestick-Data",
        schema_version="binance-coinm-continuous-klines-report-001",
    )

    def __init__(
        self,
        pair: str,
        contract_type: str,
        interval: str,
        *,
        limit: int = 500,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        timeout_seconds: float = 5.0,
        transport=None,
        base_url: str = "https://dapi.binance.com",
    ) -> None:
        pair = pair.strip().upper()
        contract_type = contract_type.strip().upper()
        interval = interval.strip()
        if not pair:
            raise ValueError("pair must be non-empty")
        if contract_type not in _CONTRACT_TYPES:
            raise ValueError("unsupported continuous-contract type")
        if not interval:
            raise ValueError("interval must be non-empty")
        if type(limit) is not int or not 1 <= limit <= _LIMIT_MAX:
            raise ValueError("limit outside report-001 documented range")
        for name, value in (("start_time", start_time), ("end_time", end_time)):
            if value is not None and (value.tzinfo is None or value.utcoffset() is None):
                raise ValueError(f"{name} must be timezone-aware")
        if start_time is not None and end_time is not None:
            start_time = start_time.astimezone(timezone.utc)
            end_time = end_time.astimezone(timezone.utc)
            if start_time > end_time:
                raise ValueError("start_time cannot be later than end_time")
            if (end_time - start_time).days > _MAX_SPAN_DAYS:
                raise ValueError("continuous-kline request span exceeds 200 days")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if not isinstance(base_url, str) or not base_url.startswith("https://"):
            raise ValueError("base_url must be HTTPS")

        self.pair = pair
        self.contract_type = contract_type
        self.interval = interval
        self.limit = limit
        self.start_time = start_time
        self.end_time = end_time
        self.timeout_seconds = timeout_seconds
        self.base_url = base_url.rstrip("/")
        self._transport = transport or _UrllibJsonTransport()

    def fetch_snapshot(self, *, as_of: datetime | None = None) -> NormalizedSnapshot:
        if as_of is not None:
            if as_of.tzinfo is None or as_of.utcoffset() is None:
                raise ValueError("as_of must be timezone-aware")
            as_of = as_of.astimezone(timezone.utc)
        params = {
            "pair": self.pair,
            "contractType": self.contract_type,
            "interval": self.interval,
            "limit": str(self.limit),
        }
        if self.start_time is not None:
            params["startTime"] = str(int(self.start_time.timestamp() * 1000))
        if self.end_time is not None:
            params["endTime"] = str(int(self.end_time.timestamp() * 1000))
        topic = f"binance-coinm-continuous-kline:{self.pair}:{self.contract_type}:{self.interval}"
        try:
            payload, received_at = self._transport.get(
                f"{self.base_url}{_ENDPOINT}", params, self.timeout_seconds
            )
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
        if not isinstance(payload, list):
            return self._failure(topic, received_at, "schema_error", "expected_list_response")
        try:
            rows = tuple(self._normalize_row(row, as_of) for row in payload)
        except _PITUnavailable as exc:
            return self._failure(topic, received_at, "pit_unavailable", str(exc))
        except ValueError as exc:
            return self._failure(topic, received_at, "schema_error", str(exc))
        return NormalizedSnapshot(
            metadata=DataSnapshotMetadata(
                source_kind=SourceKind.EXCHANGE,
                instrument_or_topic=topic,
                received_at=received_at,
                available_at=received_at,
                quality=DataQualityStatus.VALID,
                provenance=self._PROVENANCE,
            ),
            values={"pair": self.pair, "contract_type": self.contract_type, "interval": self.interval, "rows": rows},
        )

    def _normalize_row(self, row: object, as_of: datetime | None) -> tuple[object, ...]:
        if not isinstance(row, Sequence) or isinstance(row, (str, bytes, bytearray)):
            raise ValueError("kline row must be an array")
        if len(row) < 7:
            raise ValueError("kline row must contain open and close timestamps")
        try:
            open_time_ms = int(str(row[0]))
            close_time_ms = int(str(row[6]))
        except (TypeError, ValueError) as exc:
            raise ValueError("kline timestamps must be integer-like") from exc
        if open_time_ms < 0 or close_time_ms < open_time_ms:
            raise ValueError("invalid kline timestamps")
        close_at = datetime.fromtimestamp(close_time_ms / 1000, timezone.utc)
        if as_of is not None and close_at >= as_of:
            raise _PITUnavailable("candle close is not strictly before as_of")
        # Preserve all provider-defined cells; only timestamps are interpreted for PIT/closed checks.
        return tuple(row)

    def _failure(self, topic: str, received_at: datetime, error_class: str, *detail: str) -> NormalizedSnapshot:
        quality = DataQualityStatus.INVALID if error_class in {"invalid_payload", "schema_error"} else DataQualityStatus.UNAVAILABLE
        return NormalizedSnapshot(
            metadata=DataSnapshotMetadata(SourceKind.EXCHANGE, topic, received_at, available_at=received_at, quality=quality, provenance=self._PROVENANCE),
            values={"pair": self.pair, "contract_type": self.contract_type, "interval": self.interval, "error_class": error_class, "error_detail": "|".join(detail)},
        )


class _UrllibJsonTransport:
    def get(self, url: str, params: dict[str, str], timeout_seconds: float):
        from urllib.parse import urlencode
        from urllib.request import Request, build_opener
        from json import loads

        request = Request(f"{url}?{urlencode(params)}", headers={"Accept": "application/json"}, method="GET")
        with build_opener(_NoRedirectHandler()).open(request, timeout=timeout_seconds) as response:
            return loads(response.read().decode("utf-8")), datetime.now(timezone.utc)


class _PITUnavailable(ValueError):
    pass


__all__ = ["BinanceCoinMContinuousKlineDataSource"]
