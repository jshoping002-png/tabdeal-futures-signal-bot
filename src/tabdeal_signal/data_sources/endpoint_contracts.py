"""Traceable endpoint contracts derived only from existing source-verification evidence.

No new sources are added here. Known exact paths are recorded; unresolved details
remain explicitly runtime-configured instead of being inferred.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class EndpointExactness(StrEnum):
    EXACT = "exact"
    BASE_PATH = "base_path"
    RUNTIME_CONFIGURED = "runtime_configured"


@dataclass(frozen=True, slots=True)
class EndpointContract:
    source_id: str
    operation: str
    method: str
    path: str | None
    exactness: EndpointExactness
    auth_required: bool
    evidence_report: str

    def __post_init__(self) -> None:
        if not self.source_id.strip() or not self.operation.strip() or not self.method.strip():
            raise ValueError("source_id, operation and method must be non-empty")
        if self.evidence_report not in {"001", "002", "003", "004", "005", "006", "007", "008", "2040"}:
            raise ValueError("evidence_report must reference existing evidence")
        if self.exactness is EndpointExactness.EXACT and not self.path:
            raise ValueError("exact contracts require a path")
        if self.exactness is EndpointExactness.BASE_PATH and (not self.path or not self.path.endswith("/")):
            raise ValueError("base-path contracts require a slash-terminated path")
        if self.exactness is EndpointExactness.RUNTIME_CONFIGURED and self.path is not None:
            raise ValueError("runtime-configured contracts must not invent a path")
        if self.auth_required:
            raise ValueError("endpoint catalog is restricted to public read-only sources")


VERIFIED_ENDPOINT_CONTRACTS: tuple[EndpointContract, ...] = (
    EndpointContract("binance-futures-market-data", "continuous-contract-klines", "GET", "/dapi/v1/continuousKlines", EndpointExactness.EXACT, False, "001"),
    EndpointContract("bybit-futures-market-data", "kline", "GET", "/v5/market/kline", EndpointExactness.EXACT, False, "001"),
    EndpointContract("bybit-futures-market-data", "open-interest", "GET", "/v5/market/open-interest", EndpointExactness.EXACT, False, "001"),
    EndpointContract("bybit-futures-market-data", "orderbook", "GET", "/v5/market/orderbook", EndpointExactness.EXACT, False, "2040"),
    EndpointContract("bybit-futures-market-data", "funding-history", "GET", "/v5/market/funding/history", EndpointExactness.EXACT, False, "2040"),
    EndpointContract("bybit-futures-market-data", "tickers", "GET", "/v5/market/tickers", EndpointExactness.EXACT, False, "2040"),
    EndpointContract("bybit-futures-market-data", "instruments-info", "GET", "/v5/market/instruments-info", EndpointExactness.EXACT, False, "2040"),
    EndpointContract("bls-public-api", "timeseries-data", "POST", "/publicAPI/v1/timeseries/data/", EndpointExactness.EXACT, False, "001"),
    EndpointContract("binance-spot-market-data", "public-market-data", "GET", None, EndpointExactness.RUNTIME_CONFIGURED, False, "002"),
    EndpointContract("bybit-spot-market-data", "kline", "GET", "/v5/market/kline", EndpointExactness.EXACT, False, "002"),
    EndpointContract("bybit-spot-market-data", "tickers", "GET", "/v5/market/tickers", EndpointExactness.EXACT, False, "002"),
    EndpointContract("us-treasury-daily-interest-rates", "daily-rates-feed", "GET", None, EndpointExactness.RUNTIME_CONFIGURED, False, "002"),
    EndpointContract("sec-edgar-public-api", "public-json-api", "GET", None, EndpointExactness.RUNTIME_CONFIGURED, False, "002"),
    EndpointContract("okx-market-data", "public-market-data", "GET", None, EndpointExactness.RUNTIME_CONFIGURED, False, "003"),
    EndpointContract("kraken-futures-market-data", "chart-candles", "GET", "/api/charts/v1/:tick_type/:symbol/:resolution", EndpointExactness.EXACT, False, "003"),
    EndpointContract("coinbase-advanced-trade-market-data", "public-rest-market-data", "GET", None, EndpointExactness.RUNTIME_CONFIGURED, False, "003"),
    EndpointContract("deribit-market-data", "public-get-instruments", "JSON-RPC", "public/get_instruments", EndpointExactness.EXACT, False, "003"),
    EndpointContract("deribit-market-data", "public-ticker", "JSON-RPC", "public/ticker", EndpointExactness.EXACT, False, "003"),
    EndpointContract("deribit-market-data", "public-order-book", "JSON-RPC", "public/get_order_book", EndpointExactness.EXACT, False, "003"),
    EndpointContract("deribit-market-data", "tradingview-chart-data", "JSON-RPC", "public/get_tradingview_chart_data", EndpointExactness.EXACT, False, "003"),
    EndpointContract("cftc-public-reporting", "published-feed", "GET", None, EndpointExactness.RUNTIME_CONFIGURED, False, "004"),
    EndpointContract("coinmarketcap-keyless-public-api", "curated-public-api", "GET", None, EndpointExactness.RUNTIME_CONFIGURED, False, "004"),
    EndpointContract("ecb-data-portal-api", "sdmx-service", "GET", "/service/", EndpointExactness.BASE_PATH, False, "005"),
    EndpointContract("bis-statistics-api", "sdmx-rest", "GET", None, EndpointExactness.RUNTIME_CONFIGURED, False, "006"),
    EndpointContract("eurostat-rest-sdmx-api", "rest-sdmx", "GET", None, EndpointExactness.RUNTIME_CONFIGURED, False, "006"),
    EndpointContract("oecd-data-explorer-sdmx", "public-rest", "GET", "/public/rest/", EndpointExactness.BASE_PATH, False, "007"),
    EndpointContract("ny-fed-markets-data", "markets-data-api", "GET", None, EndpointExactness.RUNTIME_CONFIGURED, False, "008"),
)


def endpoint_contracts_for(source_id: str) -> tuple[EndpointContract, ...]:
    if not isinstance(source_id, str) or not source_id.strip():
        raise ValueError("source_id must be non-empty")
    return tuple(item for item in VERIFIED_ENDPOINT_CONTRACTS if item.source_id == source_id.strip())


def source_ids_with_endpoint_contracts() -> tuple[str, ...]:
    return tuple(dict.fromkeys(item.source_id for item in VERIFIED_ENDPOINT_CONTRACTS))


__all__ = [
    "EndpointContract",
    "EndpointExactness",
    "VERIFIED_ENDPOINT_CONTRACTS",
    "endpoint_contracts_for",
    "source_ids_with_endpoint_contracts",
]
