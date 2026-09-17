"""Read-only Bybit V5 Open Interest adapter."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from .bybit import JsonTransport, UrllibJsonTransport
from .contracts import (
    DataProvenance,
    DataQualityStatus,
    DataSnapshotMetadata,
    NormalizedSnapshot,
    ReadOnlyDataSource,
    SourceKind,
)

_ENDPOINT = "/v5/market/open-interest"
_CATEGORIES = {"linear", "inverse"}
_INTERVALS = {"5min", "15min", "30min", "1h", "4h", "1d"}


class BybitOpenInterestDataSource(ReadOnlyDataSource):
    """Fetch one public Bybit Open Interest history page without credentials."""

    _PROVENANCE = DataProvenance(
        source="bybit-v5-public-open-interest",
        reference="https://api.bybit.com/v5/market/open-interest",
        schema_version=(
            "bybit-v5-open-interest-docs@75994fda16e052aaad6e3fade82fd1f6fd90288e"
        ),
    )

    def __init__(
        self,
        symbol: str,
        *,
        category: str = "linear",
        interval_time: str = "5min",
        limit: int = 50,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        cursor: str | None = None,
        timeout_seconds: float = 5.0,
        transport: JsonTransport | None = None,
    ) -> None:
        symbol = symbol.strip().upper()
        category = category.strip().lower()
        interval_time = interval_time.strip()
        if not symbol:
            raise ValueError("symbol must not be empty")
        if category not in _CATEGORIES:
            raise ValueError("unsupported Bybit Open Interest category")
        if interval_time not in _INTERVALS:
            raise ValueError("unsupported Bybit Open Interest intervalTime")
        if type(limit) is not int or not 1 <= limit <= 200:
            raise ValueError("limit outside documented Bybit Open Interest range")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        for name, value in (("start_time", start_time), ("end_time", end_time)):
            if value is not None and (value.tzinfo is None or value.utcoffset() is None):
                raise ValueError(f"{name} must be timezone-aware")
        if start_time is not None and end_time is not None and start_time > end_time:
            raise ValueError("start_time cannot be later than end_time")
        if cursor is not None and (not isinstance(cursor, str) or not cursor.strip()):
            raise ValueError("cursor must be a non-empty string when supplied")

        self.symbol = symbol
        self.category = category
        self.interval_time = interval_time
        self.limit = limit
        self.start_time = start_time.astimezone(timezone.utc) if start_time else None
        self.end_time = end_time.astimezone(timezone.utc) if end_time else None
        self.cursor = cursor.strip() if cursor else None
        self.timeout_seconds = timeout_seconds
        self._transport = transport or UrllibJsonTransport()

    def fetch_snapshot(self, *, as_of: datetime | None = None) -> NormalizedSnapshot:
        if as_of is not None:
            if as_of.tzinfo is None or as_of.utcoffset() is None:
                raise ValueError("as_of must be timezone-aware")
            as_of = as_of.astimezone(timezone.utc)

        params: dict[str, str] = {
            "category": self.category,
            "symbol": self.symbol,
            "intervalTime": self.interval_time,
            "limit": str(self.limit),
        }
        if self.start_time is not None:
            params["startTime"] = str(int(self.start_time.timestamp() * 1000))
        if self.end_time is not None:
            params["endTime"] = str(int(self.end_time.timestamp() * 1000))
        if self.cursor is not None:
            params["cursor"] = self.cursor
        topic = f"open-interest:{self.category}:{self.symbol}:{self.interval_time}"

        try:
            payload, received_at = self._transport.get(
                _ENDPOINT, params, self.timeout_seconds
            )
            if received_at.tzinfo is None or received_at.utcoffset() is None:
                raise ValueError("transport received_at must be timezone-aware")
            received_at = received_at.astimezone(timezone.utc)
        except (TimeoutError, OSError) as exc:
            return self._failure(
                topic, datetime.now(timezone.utc), "transport_error", type(exc).__name__
            )
        except ValueError as exc:
            return self._failure(
                topic, datetime.now(timezone.utc), "invalid_payload", str(exc)
            )

        ret_code = payload.get("retCode")
        if type(ret_code) is not int:
            return self._failure(
                topic, received_at, "schema_error", "missing_or_non_integer_retCode"
            )
        if ret_code != 0:
            return self._failure(topic, received_at, "provider_error", str(ret_code))
        if as_of is not None and received_at > as_of:
            return self._failure(topic, received_at, "pit_unavailable", "received_after_as_of")

        try:
            values = self._normalize(payload.get("result"), as_of)
        except _PITUnavailable as exc:
            return self._failure(topic, received_at, "pit_unavailable", str(exc))
        except (TypeError, ValueError) as exc:
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
            values=values,
        )

    def _normalize(self, result: object, as_of: datetime | None) -> dict[str, object]:
        if not isinstance(result, Mapping):
            raise ValueError("result must be an object")
        rows = result.get("list")
        next_cursor = result.get("nextPageCursor", "")
        if not isinstance(rows, list):
            raise ValueError("result.list must be a list")
        if not isinstance(next_cursor, str):
            raise ValueError("nextPageCursor must be a string")
        return {
            "category": self.category,
            "symbol": self.symbol,
            "interval_time": self.interval_time,
            "rows": tuple(self._normalize_row(row, as_of) for row in rows),
            "next_page_cursor": next_cursor,
        }

    def _normalize_row(self, row: object, as_of: datetime | None) -> dict[str, object]:
        if not isinstance(row, Mapping):
            raise ValueError("open-interest row must be an object")
        if row.get("symbol") != self.symbol:
            raise ValueError("response symbol mismatch")
        open_interest = row.get("openInterest")
        timestamp = row.get("timestamp")
        if not isinstance(open_interest, str) or not open_interest.strip():
            raise ValueError("openInterest must be a non-empty string")
        try:
            decimal_value = Decimal(open_interest)
            timestamp_ms = int(str(timestamp))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise ValueError("invalid open-interest numeric/timestamp value") from exc
        if not decimal_value.is_finite() or decimal_value < 0:
            raise ValueError("openInterest must be a finite non-negative number")
        if timestamp_ms < 0:
            raise ValueError("timestamp must be non-negative")
        observed_at = datetime.fromtimestamp(timestamp_ms / 1000, timezone.utc)
        if as_of is not None and observed_at > as_of:
            raise _PITUnavailable("row observation is after as_of")

        result: dict[str, object] = {
            "symbol": self.symbol,
            "open_interest": open_interest,
            "timestamp_ms": timestamp_ms,
            "observed_at": observed_at,
        }
        single = row.get("singleOpenInterest")
        if single is not None:
            if not isinstance(single, str) or not single.strip():
                raise ValueError("singleOpenInterest must be a non-empty string when present")
            try:
                single_decimal = Decimal(single)
            except InvalidOperation as exc:
                raise ValueError("invalid singleOpenInterest value") from exc
            if not single_decimal.is_finite() or single_decimal < 0:
                raise ValueError("singleOpenInterest must be finite and non-negative")
            result["single_open_interest"] = single
        return result

    def _failure(self, topic: str, received_at: datetime, error_class: str, *detail: str) -> NormalizedSnapshot:
        quality = (
            DataQualityStatus.INVALID
            if error_class in {"invalid_payload", "schema_error"}
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


class _PITUnavailable(ValueError):
    pass


__all__ = ["BybitOpenInterestDataSource"]
