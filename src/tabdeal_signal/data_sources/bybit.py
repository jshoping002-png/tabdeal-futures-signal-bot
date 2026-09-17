"""Read-only Bybit V5 REST market-data adapter."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .contracts import (
    DataProvenance,
    DataQualityStatus,
    DataSnapshotMetadata,
    NormalizedSnapshot,
    ReadOnlyDataSource,
    SourceKind,
)

_BYBIT_ENDPOINT = "/v5/market/orderbook"
_CATEGORY_LIMITS = {
    "spot": (1, 1000),
    "linear": (1, 1000),
    "inverse": (1, 1000),
    "option": (1, 25),
}


class JsonTransport(Protocol):
    """Injectable read-only JSON transport for deterministic tests."""

    def get(
        self,
        path: str,
        params: Mapping[str, str],
        timeout_seconds: float,
    ) -> tuple[Mapping[str, object], datetime]:
        ...


class UrllibJsonTransport:
    """Minimal standard-library HTTP transport with no credential support."""

    def __init__(self, base_url: str = "https://api.bybit.com") -> None:
        self._base_url = base_url.rstrip("/")

    def get(
        self,
        path: str,
        params: Mapping[str, str],
        timeout_seconds: float,
    ) -> tuple[Mapping[str, object], datetime]:
        url = f"{self._base_url}{path}?{urlencode(params)}"
        request = Request(url, headers={"Accept": "application/json"}, method="GET")
        with urlopen(request, timeout=timeout_seconds) as response:
            received_at = datetime.now(timezone.utc)
            body = response.read()
        parsed = json.loads(body.decode("utf-8"))
        if not isinstance(parsed, Mapping):
            raise ValueError("provider JSON root must be an object")
        return parsed, received_at


class BybitOrderbookDataSource(ReadOnlyDataSource):
    """Fetch and normalize Bybit public REST orderbook snapshots only."""

    _PROVENANCE = DataProvenance(
        source="bybit-v5-public-orderbook",
        reference="https://api.bybit.com/v5/market/orderbook",
        schema_version=(
            "bybit-v5-orderbook-docs@75994fda16e052aaad6e3fade82fd1f6fd90288e"
        ),
    )

    def __init__(
        self,
        symbol: str,
        *,
        category: str = "linear",
        limit: int | None = None,
        timeout_seconds: float = 5.0,
        transport: JsonTransport | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        symbol = symbol.strip().upper()
        category = category.strip().lower()
        if not symbol:
            raise ValueError("symbol must not be empty")
        if category not in _CATEGORY_LIMITS:
            raise ValueError("unsupported Bybit category")
        low, high = _CATEGORY_LIMITS[category]
        if limit is not None and not (low <= limit <= high):
            raise ValueError("limit outside documented Bybit range")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

        self.symbol = symbol
        self.category = category
        self.limit = limit
        self.timeout_seconds = timeout_seconds
        self._transport = transport or UrllibJsonTransport()
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def fetch_snapshot(
        self, *, as_of: datetime | None = None
    ) -> NormalizedSnapshot:
        """Return one PIT-safe normalized public orderbook snapshot."""
        if as_of is not None:
            if as_of.tzinfo is None or as_of.utcoffset() is None:
                raise ValueError("as_of must be timezone-aware")
            as_of = as_of.astimezone(timezone.utc)

        params = {"category": self.category, "symbol": self.symbol}
        if self.limit is not None:
            params["limit"] = str(self.limit)
        topic = f"orderbook:{self.category}:{self.symbol}"

        try:
            payload, received_at = self._transport.get(
                _BYBIT_ENDPOINT, params, self.timeout_seconds
            )
            if received_at.tzinfo is None or received_at.utcoffset() is None:
                raise ValueError("transport received_at must be timezone-aware")
            received_at = received_at.astimezone(timezone.utc)
        except HTTPError as exc:
            return self._failure(
                topic,
                self._safe_now(),
                "rate_limited" if exc.code in (403, 429) else "http_error",
                str(exc.code),
            )
        except (TimeoutError, URLError, OSError) as exc:
            return self._failure(
                topic, self._safe_now(), "transport_error", type(exc).__name__
            )
        except json.JSONDecodeError:
            return self._failure(
                topic, self._safe_now(), "invalid_json", "json_decode_error"
            )
        except ValueError as exc:
            return self._failure(
                topic, self._safe_now(), "invalid_payload", str(exc)
            )

        ret_code = payload.get("retCode")
        if type(ret_code) is not int:
            return self._failure(
                topic, received_at, "schema_error", "missing_or_non_integer_retCode"
            )
        if ret_code != 0:
            ret_msg = payload.get("retMsg")
            return self._failure(
                topic,
                received_at,
                "rate_limited" if ret_code == 10006 else "provider_error",
                str(ret_code),
                ret_msg if isinstance(ret_msg, str) else "",
            )

        try:
            values = self._normalize(payload.get("result"), received_at, as_of)
        except _PITUnavailable as exc:
            return self._failure(topic, received_at, "pit_unavailable", str(exc))
        except (TypeError, ValueError) as exc:
            return self._failure(topic, received_at, "schema_error", str(exc))

        observed_at = datetime.fromtimestamp(
            values["system_timestamp_ms"] / 1000, timezone.utc
        )
        effective_at = datetime.fromtimestamp(
            values["matching_engine_timestamp_ms"] / 1000, timezone.utc
        )
        return NormalizedSnapshot(
            metadata=DataSnapshotMetadata(
                source_kind=SourceKind.EXCHANGE,
                instrument_or_topic=topic,
                received_at=received_at,
                observed_at=observed_at,
                effective_at=effective_at,
                available_at=received_at,
                quality=DataQualityStatus.VALID,
                provenance=self._PROVENANCE,
            ),
            values=values,
        )

    def _normalize(
        self,
        result: object,
        received_at: datetime,
        as_of: datetime | None,
    ) -> dict[str, object]:
        if not isinstance(result, Mapping):
            raise ValueError("result must be an object")

        symbol = result.get("s")
        bids = result.get("b")
        asks = result.get("a")
        ts = result.get("ts")
        update_id = result.get("u")
        cross_sequence = result.get("seq")
        matching_timestamp = result.get("cts")

        if symbol != self.symbol:
            raise ValueError("response symbol mismatch")
        if not all(
            type(value) is int
            for value in (ts, update_id, cross_sequence, matching_timestamp)
        ):
            raise ValueError("timestamp/update fields must be integers")
        if as_of is not None and received_at > as_of:
            raise _PITUnavailable("snapshot was received after as_of")

        return {
            "category": self.category,
            "symbol": symbol,
            "bids": tuple(self._levels(bids, descending=True)),
            "asks": tuple(self._levels(asks, descending=False)),
            "update_id": update_id,
            "cross_sequence": cross_sequence,
            "system_timestamp_ms": ts,
            "matching_engine_timestamp_ms": matching_timestamp,
        }

    @staticmethod
    def _levels(
        value: object, *, descending: bool
    ) -> list[tuple[Decimal, Decimal]]:
        if not isinstance(value, list):
            raise ValueError("orderbook side must be a list")
        levels: list[tuple[Decimal, Decimal]] = []
        for row in value:
            if not isinstance(row, list) or len(row) != 2:
                raise ValueError("orderbook level must contain price and size")
            try:
                price = Decimal(str(row[0]))
                size = Decimal(str(row[1]))
            except (InvalidOperation, ValueError) as exc:
                raise ValueError("invalid orderbook numeric value") from exc
            if not price.is_finite() or not size.is_finite():
                raise ValueError("orderbook numeric values must be finite")
            if price < 0 or size < 0:
                raise ValueError("orderbook numeric values must be non-negative")
            levels.append((price, size))

        prices = [price for price, _ in levels]
        if prices != sorted(prices, reverse=descending):
            raise ValueError("orderbook levels are not sorted as documented")
        return levels

    def _failure(
        self,
        topic: str,
        received_at: datetime,
        error_class: str,
        *detail: str,
    ) -> NormalizedSnapshot:
        quality = (
            DataQualityStatus.INVALID
            if error_class in {"invalid_json", "invalid_payload", "schema_error"}
            else DataQualityStatus.UNAVAILABLE
        )
        return NormalizedSnapshot(
            metadata=DataSnapshotMetadata(
                source_kind=SourceKind.EXCHANGE,
                instrument_or_topic=topic,
                received_at=received_at,
                available_at=received_at,
                quality=quality,
                provenance=self._PROVENANCE,
            ),
            values={
                "category": self.category,
                "symbol": self.symbol,
                "error_class": error_class,
                "error_detail": "|".join(detail),
            },
        )

    def _safe_now(self) -> datetime:
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("clock must return timezone-aware datetime")
        return now.astimezone(timezone.utc)


class _PITUnavailable(ValueError):
    pass


__all__ = ["BybitOrderbookDataSource", "JsonTransport", "UrllibJsonTransport"]
