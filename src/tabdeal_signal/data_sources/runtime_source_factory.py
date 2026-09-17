"""Factory for runtime-configured, read-only source adapters."""
from __future__ import annotations

from collections.abc import Mapping

from .contracts import ReadOnlyDataSource
from .public_sources import (
    CftcPublicReportingDataSource,
    CoinMarketCapKeylessDataSource,
    EurostatDataSource,
    SecEdgarDataSource,
    TreasuryDailyRatesDataSource,
    BisStatisticsDataSource,
)
from .runtime_config import RuntimeEndpointConfig
from .source_family_adapters import (
    BinanceSpotMarketDataSource,
    CoinbaseAdvancedTradeMarketDataSource,
    NyFedMarketsDataSource,
    OkxMarketDataSource,
)


_RUNTIME_ADAPTER_FACTORIES = {
    "binance-spot-market-data": BinanceSpotMarketDataSource,
    "us-treasury-daily-interest-rates": TreasuryDailyRatesDataSource,
    "sec-edgar-public-api": SecEdgarDataSource,
    "okx-market-data": OkxMarketDataSource,
    "coinbase-advanced-trade-market-data": CoinbaseAdvancedTradeMarketDataSource,
    "cftc-public-reporting": CftcPublicReportingDataSource,
    "coinmarketcap-keyless-public-api": CoinMarketCapKeylessDataSource,
    "bis-statistics-api": BisStatisticsDataSource,
    "eurostat-rest-sdmx-api": EurostatDataSource,
    "ny-fed-markets-data": NyFedMarketsDataSource,
}


def build_runtime_source(
    config: RuntimeEndpointConfig,
    *,
    topic: str,
    schema_version: str,
    query: Mapping[str, str] | None = None,
    transport: object | None = None,
) -> ReadOnlyDataSource:
    """Build exactly one existing runtime-configured adapter.

    The factory does not create new source IDs, infer endpoints, or add
    authentication. Coinbase keeps its explicitly supplied host allowlist
    because its reports did not establish one canonical host in this project.
    """
    if not isinstance(config, RuntimeEndpointConfig):
        raise TypeError("config must be RuntimeEndpointConfig")
    adapter = _RUNTIME_ADAPTER_FACTORIES.get(config.source_id)
    if adapter is None:
        raise KeyError(config.source_id)
    kwargs = {
        "endpoint": config.endpoint,
        "topic": topic,
        "schema_version": schema_version,
        "query": query,
    }
    if transport is not None:
        kwargs["transport"] = transport
    if config.source_id == "coinbase-advanced-trade-market-data":
        kwargs["allowed_hosts"] = config.allowed_hosts
    return adapter(**kwargs)


__all__ = ["build_runtime_source"]
