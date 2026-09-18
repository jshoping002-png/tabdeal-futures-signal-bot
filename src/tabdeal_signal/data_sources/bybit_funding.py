"""Read-only Bybit V5 Funding Rate History adapter."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from urllib.error import HTTPError, URLError

from .bybit import JsonTransport, UrllibJsonTransport
from .contracts import (
    DataProvenance,
    DataQualityStatus,
    DataSnapshotMetadata,
    NormalizedSnapshot,
    ReadOnlyDataSource,
    SourceKind,
)

_ENDPOINT = "/v5/market/funding/history"
_CATEGORIES = {"linear", "inverse"}


class BybitFundingRateDataSource(ReadOnlyDataSource):
    """Fetch one public Bybit Funding Rate History page without credentials."""

    _PROVENANCE = DataProvenance(
        source="bybit-v5-public-funding-history",
        reference="https://api.bybit.com/v5/market/funding/history",
        schema_version=(
            "bybit-v5-funding-history-docs@75994fda16e052aaad6e3fade82fd1f6fd90288e"
        ),
    )

    def __init__(
        self,
        symbol: str,
        *,
        category: str = "linear",
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 50,
        timeout_seconds: float = 5.0,
        transport: JsonTransport | None = None,
    ) -> None:
        symbol = symbol.strip().upper()
        category = category.strip().lower()
        if not symbol:
            raise ValueError("symbol must not be empty")
        if category not in _CATEGORIES:
            raise ValueError("unsupported Bybit Funding Rate category")
        if type(limit) is not int or not 1 <= limit <= 200:
            raise ValueError("limit outside documented Bybit Funding Rate range")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        for name, value in (("start_time", start_time), ("end_time", end_time)):
            if value is not None and (value.tzinfo is None or value.utcoffset() is None):
                raise ValueError(f"{name} must be timezone-aware")
        if start_time is not None and end_time is None:
            raise ValueError("start_time requires end_time for the documented Bybit funding-history request")
        if start_time is not None and end_time is not None and start_time > end_time:
            raise ValueError("start_time cannot be later than end_time")

        self.symbol = symbol
        self.category = category
        self.start_time = start_time.astimezone(timezone.utc) if start_time else None
        self.end_time = end_time.astimezone(timezone.utc) if end_time else None
        self.limit = limit
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
            "limit": str(self.limit),
        }
        if self.start_time is not None:
            params["startTime"] = str(int(self.start_time.timestamp() * 1000))
        if self.end_time is not None:
            params["endTime"] = str(int(self.end_time.timestamp() * 1000))
        topic = f"funding-rate-history:{self.category}:{self.symbol}"

        try:
            payload, received_at = self._transport.get(
                _ENDPOINT, params, self.timeout_seconds
            )
            if received_at.tzinfo is None or received_at.utcoffset() is None:
                raise ValueError("transport received_at must be timezone-aware")
            received_at = received_at.astimezone(timezone.utc)
        except HTTPError as exc:
            return self._failure(
                topic,
                datetime.now(timezone.utc),
                "rate_limited" if exc.code in (403, 429) else "http_error",
                str(exc.code),
            )
        except (TimeoutError, URLError, OSError) as exc:
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
            return self._failure(
                topic,
                received_at,
                "rate_limited" if ret_code == 10006 else "provider_error",
                str(ret_code),
            )
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
        if not isinstance(rows, list):
            raise ValueError("result.list must be a list")

        normalized_rows: list[dict[str, object]] = []
        for row in rows:
            if not isinstance(row, Mapping):
                raise ValueError("funding-rate row must be an object")
            if row.get("symbol") != self.symbol:
                raise ValueError("response symbol mismatch")
            funding_rate = row.get("fundingRate")
            timestamp = row.get("fundingRateTimestamp")
            if not isinstance(funding_rate, str) or not funding_rate.strip():
                raise ValueError("fundingRate must be a non-empty string")
            if not isinstance(timestamp, str) or not timestamp.strip():
                raise ValueError("fundingRateTimestamp must be a non-empty string")
            try:
                rate = Decimal(funding_rate)
                timestamp_ms = int(timestamp)
            except (InvalidOperation, ValueError) as exc:
                raise ValueError("invalid funding-rate numeric/timestamp value") from exc
            if not rate.is_finite():
                raise ValueError("fundingRate must be finite")
            if timestamp_ms < 0:
                raise ValueError("fundingRateTimestamp must be non-negative")
            observed_at = datetime.fromtimestamp(timestamp_ms / 1000, timezone.utc)
            if as_of is not None and observed_at > as_of:
                raise _PITUnavailable("funding-rate observation is after as_of")
            normalized_rows.append(
                {
                    "symbol": self.symbol,
                    "funding_rate": funding_rate,
                    "funding_rate_timestamp_ms": timestamp_ms,
                    "observed_at": observed_at,
                }
            )

        return {
            "category": self.category,
            "symbol": self.symbol,
            "rows": tuple(normalized_rows),
        }

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


__all__ = ["BybitFundingRateDataSource"]
