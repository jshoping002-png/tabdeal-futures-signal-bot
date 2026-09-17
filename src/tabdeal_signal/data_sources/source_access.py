"""Operational lifecycle ledger for verified source families."""
from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum


class SourceLifecycle(StrEnum):
    DOCUMENTED = "documented"
    ACCESS_CONFIGURED = "access_configured"
    ADAPTER_BUILT = "adapter_built"
    LIVE_VERIFIED = "live_verified"
    PRODUCTION_READY = "production_ready"
    ACTIVE = "active"


@dataclass(frozen=True, slots=True)
class SourceAccessSpec:
    source_id: str
    name: str
    reports: tuple[str, ...]
    lifecycle: SourceLifecycle
    adapter_classes: tuple[str, ...] = ()
    verified_hosts: tuple[str, ...] = ()
    adapter_scope: tuple[str, ...] = ()
    exact_endpoint_required: bool = True
    strategy_authorized: bool = False
    trading_enabled: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise ValueError("source_id must be a non-empty string")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("name must be a non-empty string")
        if not self.reports:
            raise ValueError("reports must not be empty")
        if not isinstance(self.lifecycle, SourceLifecycle):
            raise ValueError("lifecycle must be SourceLifecycle")
        if self.strategy_authorized or self.trading_enabled:
            raise ValueError("source ledger cannot authorize strategy or trading")
        if any(not isinstance(item, str) or not item.strip() for item in self.reports):
            raise ValueError("reports must contain non-empty strings")
        if any(not isinstance(item, str) or not item.strip() for item in self.adapter_classes):
            raise ValueError("adapter_classes must contain non-empty strings")
        if any(not isinstance(item, str) or not item.strip() for item in self.verified_hosts):
            raise ValueError("verified_hosts must contain non-empty strings")
        if any(not isinstance(item, str) or not item.strip() for item in self.adapter_scope):
            raise ValueError("adapter_scope must contain non-empty strings")

    @property
    def is_operationally_usable(self) -> bool:
        return self.lifecycle is SourceLifecycle.ADAPTER_BUILT and bool(self.adapter_classes and self.adapter_scope)


VERIFIED_SOURCE_ACCESS_SPECS: tuple[SourceAccessSpec, ...] = (
    SourceAccessSpec(
        "binance-futures-market-data", "Binance Futures Market Data", ("001",), SourceLifecycle.ADAPTER_BUILT,
        adapter_classes=("BinanceCoinMContinuousKlineDataSource",), verified_hosts=("dapi.binance.com", "developers.binance.com"),
        adapter_scope=("Coin-M public continuous-contract klines",),
    ),
    SourceAccessSpec(
        "bybit-futures-market-data", "Bybit Futures Market Data", ("001", "2040"), SourceLifecycle.ADAPTER_BUILT,
        adapter_classes=("BybitKlineDataSource", "BybitOrderbookDataSource", "BybitOpenInterestDataSource", "BybitFundingRateDataSource", "BybitTickersDataSource", "BybitInstrumentsInfoDataSource"),
        verified_hosts=("api.bybit.com", "bybit-exchange.github.io"),
        adapter_scope=("public REST kline", "public REST orderbook", "public REST open interest", "public REST funding rate history", "public REST tickers", "public REST instruments info"),
    ),
    SourceAccessSpec("bls-public-api", "U.S. Bureau of Labor Statistics Public Data API", ("001",), SourceLifecycle.ADAPTER_BUILT, adapter_classes=("BlsPublicApiDataSource",), verified_hosts=("api.bls.gov", "bls.gov"), adapter_scope=("public JSON envelope; exact series/PIT contract runtime-configured",)),
    SourceAccessSpec("binance-spot-market-data", "Binance Spot Market Data", ("002",), SourceLifecycle.DOCUMENTED, verified_hosts=("data-api.binance.vision", "developers.binance.com"), adapter_scope=("public market-data boundary",)),
    SourceAccessSpec("bybit-spot-market-data", "Bybit Spot Market Data", ("002",), SourceLifecycle.ADAPTER_BUILT, adapter_classes=("BybitKlineDataSource", "BybitTickersDataSource"), verified_hosts=("api.bybit.com",), adapter_scope=("public REST kline", "public REST tickers")),
    SourceAccessSpec("us-treasury-daily-interest-rates", "U.S. Treasury Daily Interest-Rate Data", ("002",), SourceLifecycle.ADAPTER_BUILT, adapter_classes=("TreasuryDailyRatesDataSource",), verified_hosts=("treasury.gov",), adapter_scope=("official XML feed envelope")),
    SourceAccessSpec("sec-edgar-public-api", "SEC EDGAR Public APIs", ("002",), SourceLifecycle.ADAPTER_BUILT, adapter_classes=("SecEdgarDataSource",), verified_hosts=("data.sec.gov",), adapter_scope=("public JSON submissions/XBRL envelope")),
    SourceAccessSpec("okx-market-data", "OKX Market Data", ("003",), SourceLifecycle.DOCUMENTED, verified_hosts=("okx.com",), adapter_scope=("public market-data endpoint family; exact project endpoint contract pending",)),
    SourceAccessSpec("kraken-futures-market-data", "Kraken Futures Market Data", ("003",), SourceLifecycle.ADAPTER_BUILT, adapter_classes=("KrakenFuturesPublicCandleDataSource",), verified_hosts=("futures.kraken.com", "docs.kraken.com"), adapter_scope=("public futures chart candles: spot/mark/trade ticks")),
    SourceAccessSpec("coinbase-advanced-trade-market-data", "Coinbase Advanced Trade Market Data", ("003",), SourceLifecycle.DOCUMENTED, verified_hosts=("docs.cdp.coinbase.com",), adapter_scope=("public Advanced Trade market-data boundary; derivatives not assumed",)),
    SourceAccessSpec("deribit-market-data", "Deribit Market Data", ("003",), SourceLifecycle.DOCUMENTED, verified_hosts=("docs.deribit.com",), adapter_scope=("public market-data boundary",)),
    SourceAccessSpec("cftc-public-reporting", "CFTC Commitments of Traders / Public Reporting", ("004",), SourceLifecycle.ADAPTER_BUILT, adapter_classes=("CftcPublicReportingDataSource",), verified_hosts=("publicreporting.cftc.gov",), adapter_scope=("published feed/text envelope",)),
    SourceAccessSpec("coinmarketcap-keyless-public-api", "CoinMarketCap Keyless Public API", ("004",), SourceLifecycle.ADAPTER_BUILT, adapter_classes=("CoinMarketCapKeylessDataSource",), verified_hosts=("pro-api.coinmarketcap.com",), adapter_scope=("curated public JSON envelope; rate-limited",)),
    SourceAccessSpec("ecb-data-portal-api", "European Central Bank Data Portal API", ("005",), SourceLifecycle.ADAPTER_BUILT, adapter_classes=("EcbSdmxDataSource",), verified_hosts=("data-api.ecb.europa.eu", "ecb.europa.eu"), adapter_scope=("public SDMX/text envelope",)),
    SourceAccessSpec("bis-statistics-api", "Bank for International Settlements Statistics API", ("006",), SourceLifecycle.ADAPTER_BUILT, adapter_classes=("BisStatisticsDataSource",), verified_hosts=("stats.bis.org",), adapter_scope=("public SDMX/text envelope",)),
    SourceAccessSpec("eurostat-rest-sdmx-api", "Eurostat REST / SDMX APIs", ("006",), SourceLifecycle.ADAPTER_BUILT, adapter_classes=("EurostatDataSource",), verified_hosts=("ec.europa.eu",), adapter_scope=("public REST/SDMX text envelope",)),
    SourceAccessSpec("oecd-data-explorer-sdmx", "OECD Data Explorer SDMX API", ("007",), SourceLifecycle.DOCUMENTED, verified_hosts=("sdmx.oecd.org", "oecd.org"), adapter_scope=("public SDMX endpoint family; exact dataset/series contract pending",)),
    SourceAccessSpec("ny-fed-markets-data", "Federal Reserve Bank of New York Markets Data APIs", ("008",), SourceLifecycle.DOCUMENTED, verified_hosts=("markets.newyorkfed.org", "newyorkfed.org"), adapter_scope=("public markets-data API family; route-by-route auth contract pending",)),
)


def get_source_access_spec(source_id: str) -> SourceAccessSpec:
    if not isinstance(source_id, str) or not source_id.strip():
        raise ValueError("source_id must be a non-empty string")
    for spec in VERIFIED_SOURCE_ACCESS_SPECS:
        if spec.source_id == source_id.strip():
            return spec
    raise KeyError(source_id.strip())


def source_ids() -> tuple[str, ...]:
    return tuple(spec.source_id for spec in VERIFIED_SOURCE_ACCESS_SPECS)


__all__ = ["SourceAccessSpec", "SourceLifecycle", "VERIFIED_SOURCE_ACCESS_SPECS", "get_source_access_spec", "source_ids"]
