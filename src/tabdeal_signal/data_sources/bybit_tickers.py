"""Read-only Bybit V5 Tickers adapter."""

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

_ENDPOINT = "/v5/market/tickers"
_CATEGORIES = {"spot", "linear", "inverse", "option"}
_NUMERIC_FIELDS = (
    "lastPrice", "indexPrice", "markPrice", "prevPrice24h", "price24hPcnt",
    "highPrice24h", "lowPrice24h", "prevPrice1h", "openInterest", "openInterestValue",
    "singleOpenInterest", "singleOpenInterestValue", "turnover24h", "volume24h",
    "fundingRate", "nextFundingTime", "predictedDeliveryPrice", "basisRate", "basis",
    "deliveryFeeRate", "ask1Size", "bid1Price", "ask1Price", "bid1Size",
    "preOpenPrice", "preQty", "fundingIntervalHour", "fundingCap", "basisRateYear",
)


class BybitTickersDataSource(ReadOnlyDataSource):
    """Fetch the latest public Bybit ticker snapshot for one query scope."""

    _PROVENANCE = DataProvenance(
        source="bybit-v5-public-tickers",
        reference="https://api.bybit.com/v5/market/tickers",
        schema_version="bybit-v5-tickers-docs@75994fda16e052aaad6e3fade82fd1f6fd90288e",
    )

    def __init__(
        self,
        *,
        category: str = "linear",
        symbol: str | None = None,
        base_coin: str | None = None,
        exp_date: str | None = None,
        timeout_seconds: float = 5.0,
        transport: JsonTransport | None = None,
    ) -> None:
        category = category.strip().lower()
        if category not in _CATEGORIES:
            raise ValueError("unsupported Bybit ticker category")
        if symbol is not None:
            symbol = symbol.strip().upper()
            if not symbol:
                raise ValueError("symbol must not be empty")
        if base_coin is not None:
            base_coin = base_coin.strip().upper()
            if not base_coin:
                raise ValueError("base_coin must not be empty")
            if category != "option":
                raise ValueError("baseCoin is documented only for option tickers")
        if exp_date is not None:
            exp_date = exp_date.strip().upper()
            if not exp_date:
                raise ValueError("exp_date must not be empty")
            if category != "option":
                raise ValueError("expDate is documented only for option tickers")
        if category == "option" and symbol is None and base_coin is None:
            raise ValueError("option tickers require symbol or baseCoin")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

        self.category = category
        self.symbol = symbol
        self.base_coin = base_coin
        self.exp_date = exp_date
        self.timeout_seconds = timeout_seconds
        self._transport = transport or UrllibJsonTransport()

    def fetch_snapshot(self, *, as_of: datetime | None = None) -> NormalizedSnapshot:
        if as_of is not None:
            if as_of.tzinfo is None or as_of.utcoffset() is None:
                raise ValueError("as_of must be timezone-aware")
            as_of = as_of.astimezone(timezone.utc)
        params: dict[str, str] = {"category": self.category}
        if self.symbol is not None:
            params["symbol"] = self.symbol
        if self.base_coin is not None:
            params["baseCoin"] = self.base_coin
        if self.exp_date is not None:
            params["expDate"] = self.exp_date
        topic = f"tickers:{self.category}:{self.symbol or '*'}"
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

    def _normalize(self, result: object) -> dict[str, object]:
        if not isinstance(result, Mapping):
            raise ValueError("result must be an object")
        if result.get("category") not in (None, self.category):
            raise ValueError("response category mismatch")
        rows = result.get("list")
        if not isinstance(rows, list):
            raise ValueError("result.list must be a list")
        normalized: list[dict[str, object]] = []
        for row in rows:
            if not isinstance(row, Mapping):
                raise ValueError("ticker row must be an object")
            row_symbol = row.get("symbol")
            if not isinstance(row_symbol, str) or not row_symbol.strip():
                raise ValueError("ticker row symbol must be a non-empty string")
            row_symbol = row_symbol.strip().upper()
            if self.symbol is not None and row_symbol != self.symbol:
                raise ValueError("response symbol mismatch")
            clean = {"symbol": row_symbol}
            for field in _NUMERIC_FIELDS:
                value = row.get(field)
                if value is not None:
                    if not isinstance(value, str):
                        raise ValueError(f"ticker {field} must be a string when present")
                    if value:
                        try:
                            parsed = Decimal(value)
                        except InvalidOperation as exc:
                            raise ValueError(f"invalid ticker numeric value for {field}") from exc
                        if not parsed.is_finite():
                            raise ValueError(f"ticker numeric value for {field} must be finite")
                clean[field] = value
            for key in ("status", "settleCoin", "deliveryTime", "basisRateYear", "curPreListingPhase"):
                if key in row:
                    clean[key] = row[key]
            normalized.append(clean)
        return {"category": self.category, "rows": tuple(normalized)}

    def _failure(self, topic: str, received_at: datetime, error_class: str, *detail: str) -> NormalizedSnapshot:
        quality = DataQualityStatus.INVALID if error_class in {"invalid_payload", "schema_error"} else DataQualityStatus.UNAVAILABLE
        return NormalizedSnapshot(
            metadata=DataSnapshotMetadata(SourceKind.EXCHANGE, topic, received_at, available_at=received_at, quality=quality, provenance=self._PROVENANCE),
            values={"category": self.category, "symbol": self.symbol, "error_class": error_class, "error_detail": "|".join(detail)},
        )


__all__ = ["BybitTickersDataSource"]
