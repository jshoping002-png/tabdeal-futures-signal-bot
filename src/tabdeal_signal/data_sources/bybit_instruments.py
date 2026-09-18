"""Read-only Bybit V5 Instruments Info adapter."""

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

_ENDPOINT = "/v5/market/instruments-info"
_CATEGORIES = {"spot", "linear", "inverse", "option"}


class BybitInstrumentsInfoDataSource(ReadOnlyDataSource):
    """Fetch one public Bybit Instruments Info page with documented pagination."""

    _PROVENANCE = DataProvenance(
        source="bybit-v5-public-instruments-info",
        reference="https://api.bybit.com/v5/market/instruments-info",
        schema_version="bybit-v5-instruments-info-docs@75994fda16e052aaad6e3fade82fd1f6fd90288e",
    )

    def __init__(
        self,
        *,
        category: str = "linear",
        symbol: str | None = None,
        symbol_type: str | None = None,
        status: str | None = None,
        base_coin: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        timeout_seconds: float = 5.0,
        transport: JsonTransport | None = None,
    ) -> None:
        category = category.strip().lower()
        if category not in _CATEGORIES:
            raise ValueError("unsupported Bybit instruments-info category")
        if category == "spot":
            if limit is not None or cursor is not None:
                raise ValueError("spot Instruments Info does not support limit or cursor pagination")
        else:
            if limit is None:
                limit = 500
            if type(limit) is not int or not 1 <= limit <= 1000:
                raise ValueError("limit outside documented Bybit Instruments Info range")
        if base_coin is not None and category == "spot":
            raise ValueError("baseCoin applies only to linear, inverse and option")
        self.category = category
        self.symbol = self._normalize_optional_upper(symbol, "symbol")
        self.symbol_type = self._normalize_optional(symbol_type, "symbol_type")
        self.status = self._normalize_optional(status, "status")
        self.base_coin = self._normalize_optional_upper(base_coin, "base_coin")
        if cursor is not None and (not isinstance(cursor, str) or not cursor.strip()):
            raise ValueError("cursor must be a non-empty string when supplied")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.limit = limit
        self.cursor = cursor.strip() if cursor else None
        self.timeout_seconds = timeout_seconds
        self._transport = transport or UrllibJsonTransport()

    @staticmethod
    def _normalize_optional(value: str | None, name: str) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError(f"{name} must not be empty")
        return value

    @classmethod
    def _normalize_optional_upper(cls, value: str | None, name: str) -> str | None:
        value = cls._normalize_optional(value, name)
        return value.upper() if value is not None else None

    def fetch_snapshot(self, *, as_of: datetime | None = None) -> NormalizedSnapshot:
        if as_of is not None:
            if as_of.tzinfo is None or as_of.utcoffset() is None:
                raise ValueError("as_of must be timezone-aware")
            as_of = as_of.astimezone(timezone.utc)
        params: dict[str, str] = {"category": self.category}
        if self.limit is not None:
            params["limit"] = str(self.limit)
        for key, value in (
            ("symbol", self.symbol), ("symbolType", self.symbol_type),
            ("status", self.status), ("baseCoin", self.base_coin), ("cursor", self.cursor),
        ):
            if value is not None:
                params[key] = value
        topic = f"instruments-info:{self.category}:{self.symbol or '*'}"
        try:
            payload, received_at = self._transport.get(_ENDPOINT, params, self.timeout_seconds)
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
        if type(payload.get("retCode")) is not int:
            return self._failure(topic, received_at, "schema_error", "missing_or_non_integer_retCode")
        if payload["retCode"] != 0:
            return self._failure(
                topic,
                received_at,
                "rate_limited" if payload["retCode"] == 10006 else "provider_error",
                str(payload["retCode"]),
            )
        try:
            values = self._normalize(payload.get("result"))
        except ValueError as exc:
            return self._failure(topic, received_at, "schema_error", str(exc))
        return NormalizedSnapshot(
            metadata=DataSnapshotMetadata(SourceKind.EXCHANGE, topic, received_at, available_at=received_at, quality=DataQualityStatus.VALID, provenance=self._PROVENANCE),
            values=values,
        )

    def _normalize(self, result: object) -> dict[str, object]:
        if not isinstance(result, Mapping):
            raise ValueError("result must be an object")
        if result.get("category") not in (None, self.category):
            raise ValueError("response category mismatch")
        rows = result.get("list")
        if not isinstance(rows, list):
            raise ValueError("result.list must be a list")
        next_cursor = result.get("nextPageCursor", "")
        if not isinstance(next_cursor, str):
            raise ValueError("nextPageCursor must be a string")
        normalized = [self._normalize_row(row) for row in rows]
        if self.category == "spot" and next_cursor:
            raise ValueError("spot Instruments Info must not return pagination cursor")
        return {"category": self.category, "rows": tuple(normalized), "next_page_cursor": next_cursor}

    def _normalize_row(self, row: object) -> dict[str, object]:
        if not isinstance(row, Mapping):
            raise ValueError("instrument row must be an object")
        symbol = row.get("symbol")
        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("instrument symbol must be a non-empty string")
        symbol = symbol.strip().upper()
        if self.symbol is not None and symbol != self.symbol:
            raise ValueError("response symbol mismatch")
        out: dict[str, object] = {"symbol": symbol}
        for key in ("symbolId", "contractType", "status", "baseCoin", "quoteCoin", "symbolType", "settleCoin", "fundingInterval", "priceScale", "launchTime", "deliveryTime"):
            if key in row:
                out[key] = row[key]
        for key in ("launchTime", "deliveryTime", "fundingInterval", "symbolId"):
            value = out.get(key)
            if value is not None:
                try:
                    int(str(value))
                except (TypeError, ValueError) as exc:
                    raise ValueError(f"instrument {key} must be integer-like") from exc
        for nested_key in ("priceFilter", "lotSizeFilter", "leverageFilter"):
            if nested_key in row:
                nested = row[nested_key]
                if not isinstance(nested, Mapping):
                    raise ValueError(f"instrument {nested_key} must be an object")
                out[nested_key] = dict(nested)
        for key in ("tickSize", "minOrderQty", "qtyStep", "maxOrderQty"):
            nested = out.get("priceFilter") if key == "tickSize" else out.get("lotSizeFilter")
            if isinstance(nested, Mapping) and key in nested:
                value = nested[key]
                if not isinstance(value, str):
                    raise ValueError(f"instrument {key} must be a string when present")
                try:
                    number = Decimal(value)
                except InvalidOperation as exc:
                    raise ValueError(f"invalid instrument numeric value for {key}") from exc
                if not number.is_finite() or number < 0:
                    raise ValueError(f"instrument numeric value for {key} must be finite and non-negative")
        return out

    def _failure(self, topic: str, received_at: datetime, error_class: str, *detail: str) -> NormalizedSnapshot:
        quality = DataQualityStatus.INVALID if error_class in {"invalid_payload", "schema_error"} else DataQualityStatus.UNAVAILABLE
        return NormalizedSnapshot(DataSnapshotMetadata(SourceKind.EXCHANGE, topic, received_at, available_at=received_at, quality=quality, provenance=self._PROVENANCE), {"category": self.category, "symbol": self.symbol, "error_class": error_class, "error_detail": "|".join(detail)})


__all__ = ["BybitInstrumentsInfoDataSource"]
