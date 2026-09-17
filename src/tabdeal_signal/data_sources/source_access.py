"""Operational lifecycle ledger for verified source families.

The ledger turns the existing source-verification history into executable,
read-only metadata. It does not activate providers, invent endpoints, or
authorize strategy consumption.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SourceLifecycle(StrEnum):
    """Operational lifecycle without implying production activation."""

    DOCUMENTED = "documented"
    ACCESS_CONFIGURED = "access_configured"
    ADAPTER_BUILT = "adapter_built"
    LIVE_VERIFIED = "live_verified"
    PRODUCTION_READY = "production_ready"
    ACTIVE = "active"


@dataclass(frozen=True, slots=True)
class SourceAccessSpec:
    """Source-family operationalization metadata derived from existing reports."""

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
        for field_name in ("source_id", "name"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        if not self.reports:
            raise ValueError("reports must not be empty")
        if not isinstance(self.lifecycle, SourceLifecycle):
            raise ValueError("lifecycle must be SourceLifecycle")
        if self.strategy_authorized:
            raise ValueError("source ledger cannot authorize strategy inputs")
        if self.trading_enabled:
            raise ValueError("source ledger cannot enable trading")
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
        """True only for a built adapter with an explicitly bounded scope."""

        return self.lifecycle is SourceLifecycle.ADAPTER_BUILT and bool(
            self.adapter_classes and self.adapter_scope
        )


VERIFIED_SOURCE_ACCESS_SPECS: tuple[SourceAccessSpec, ...] = (
    SourceAccessSpec(
        source_id="binance-futures-market-data",
        name="Binance Futures Market Data",
        reports=("001",),
        lifecycle=SourceLifecycle.DOCUMENTED,
        verified_hosts=("developers.binance.com",),
        adapter_scope=("continuous-contract klines documented; exact project endpoint contract pending",),
    ),
    SourceAccessSpec(
        source_id="bybit-futures-market-data",
        name="Bybit Futures Market Data",
        reports=("001", "2040"),
        lifecycle=SourceLifecycle.ADAPTER_BUILT,
        adapter_classes=("BybitKlineDataSource", "BybitOrderbookDataSource"),
        verified_hosts=("api.bybit.com", "bybit-exchange.github.io"),
        adapter_scope=("public REST kline", "public REST orderbook"),
    ),
    SourceAccessSpec(
        source_id="bls-public-api",
        name="U.S. Bureau of Labor Statistics Public Data API",
        reports=("001",),
        lifecycle=SourceLifecycle.ADAPTER_BUILT,
        adapter_classes=("BlsPublicApiDataSource",),
        verified_hosts=("api.bls.gov", "bls.gov"),
        adapter_scope=("public JSON envelope; exact series/PIT contract remains runtime-configured",),
    ),
    SourceAccessSpec(
        source_id="binance-spot-market-data",
        name="Binance Spot Market Data",
        reports=("002",),
        lifecycle=SourceLifecycle.DOCUMENTED,
        verified_hosts=("data-api.binance.vision", "developers.binance.com"),
        adapter_scope=("public market-data boundary",),
    ),
    SourceAccessSpec(
        source_id="bybit-spot-market-data",
        name="Bybit Spot Market Data",
        reports=("002",),
        lifecycle=SourceLifecycle.ADAPTER_BUILT,
        adapter_classes=("BybitKlineDataSource",),
        verified_hosts=("api.bybit.com",),
        adapter_scope=("public REST kline with category=spot",),
    ),
    SourceAccessSpec(
        source_id="us-treasury-daily-interest-rates",
        name="U.S. Treasury Daily Interest-Rate Data",
        reports=("002",),
        lifecycle=SourceLifecycle.ADAPTER_BUILT,
        adapter_classes=("TreasuryDailyRatesDataSource",),
        verified_hosts=("home.treasury.gov",),
        adapter_scope=("official XML feed envelope",),
    ),
    SourceAccessSpec(
        source_id="sec-edgar-public-api",
        name="SEC EDGAR Public APIs",
        reports=("002",),
        lifecycle=SourceLifecycle.ADAPTER_BUILT,
        adapter_classes=("SecEdgarDataSource",),
        verified_hosts=("data.sec.gov",),
        adapter_scope=("public JSON submissions/XBRL envelope",),
    ),
    SourceAccessSpec(
        source_id="okx-market-data",
        name="OKX Market Data",
        reports=("003",),
        lifecycle=SourceLifecycle.DOCUMENTED,
        verified_hosts=("okx.com",),
        adapter_scope=("public market-data endpoint family; exact project endpoint contract pending",),
    ),
    SourceAccessSpec(
        source_id="kraken-futures-market-data",
        name="Kraken Futures Market Data",
        reports=("003",),
        lifecycle=SourceLifecycle.DOCUMENTED,
        verified_hosts=("docs.kraken.com",),
        adapter_scope=("public futures candles/analytics documented",),
    ),
    SourceAccessSpec(
        source_id="coinbase-advanced-trade-market-data",
        name="Coinbase Advanced Trade Market Data",
        reports=("003",),
        lifecycle=SourceLifecycle.DOCUMENTED,
        verified_hosts=("docs.cdp.coinbase.com",),
        adapter_scope=("public Advanced Trade market-data boundary; derivatives not assumed",),
    ),
    SourceAccessSpec(
        source_id="deribit-market-data",
        name="Deribit Market Data",
        reports=("003",),
        lifecycle=SourceLifecycle.DOCUMENTED,
        verified_hosts=("docs.deribit.com",),
        adapter_scope=("public market-data boundary",),
    ),
    SourceAccessSpec(
        source_id="cftc-public-reporting",
        name="CFTC Commitments of Traders / Public Reporting",
        reports=("004",),
        lifecycle=SourceLifecycle.ADAPTER_BUILT,
        adapter_classes=("CftcPublicReportingDataSource",),
        verified_hosts=("publicreporting.cftc.gov", "cftc.gov"),
        adapter_scope=("published feed/text envelope",),
    ),
    SourceAccessSpec(
        source_id="coinmarketcap-keyless-public-api",
        name="CoinMarketCap Keyless Public API",
        reports=("004",),
        lifecycle=SourceLifecycle.ADAPTER_BUILT,
        adapter_classes=("CoinMarketCapKeylessDataSource",),
        verified_hosts=("pro-api.coinmarketcap.com",),
        adapter_scope=("curated public JSON envelope; rate-limited",),
    ),
    SourceAccessSpec(
        source_id="ecb-data-portal-api",
        name="European Central Bank Data Portal API",
        reports=("005",),
        lifecycle=SourceLifecycle.ADAPTER_BUILT,
        adapter_classes=("EcbSdmxDataSource",),
        verified_hosts=("data-api.ecb.europa.eu", "ecb.europa.eu"),
        adapter_scope=("public SDMX/text envelope",),
    ),
    SourceAccessSpec(
        source_id="bis-statistics-api",
        name="Bank for International Settlements Statistics API",
        reports=("006",),
        lifecycle=SourceLifecycle.ADAPTER_BUILT,
        adapter_classes=("BisStatisticsDataSource",),
        verified_hosts=("stats.bis.org",),
        adapter_scope=("public SDMX/text envelope",),
    ),
    SourceAccessSpec(
        source_id="eurostat-rest-sdmx-api",
        name="Eurostat REST / SDMX APIs",
        reports=("006",),
        lifecycle=SourceLifecycle.ADAPTER_BUILT,
        adapter_classes=("EurostatDataSource",),
        verified_hosts=("ec.europa.eu",),
        adapter_scope=("public REST/SDMX text envelope",),
    ),
    SourceAccessSpec(
        source_id="oecd-data-explorer-sdmx",
        name="OECD Data Explorer SDMX API",
        reports=("007",),
        lifecycle=SourceLifecycle.DOCUMENTED,
        verified_hosts=("sdmx.oecd.org", "oecd.org"),
        adapter_scope=("public SDMX endpoint family; exact dataset/series contract pending",),
    ),
    SourceAccessSpec(
        source_id="ny-fed-markets-data",
        name="Federal Reserve Bank of New York Markets Data APIs",
        reports=("008",),
        lifecycle=SourceLifecycle.DOCUMENTED,
        verified_hosts=("markets.newyorkfed.org", "newyorkfed.org"),
        adapter_scope=("public markets-data API family; route-by-route auth contract pending",),
    ),
)


def get_source_access_spec(source_id: str) -> SourceAccessSpec:
    """Return one source spec by stable identifier."""

    if not isinstance(source_id, str) or not source_id.strip():
        raise ValueError("source_id must be a non-empty string")
    normalized = source_id.strip()
    for spec in VERIFIED_SOURCE_ACCESS_SPECS:
        if spec.source_id == normalized:
            return spec
    raise KeyError(normalized)


def source_ids() -> tuple[str, ...]:
    """Return stable ids in deterministic order."""

    return tuple(spec.source_id for spec in VERIFIED_SOURCE_ACCESS_SPECS)


__all__ = [
    "SourceAccessSpec",
    "SourceLifecycle",
    "VERIFIED_SOURCE_ACCESS_SPECS",
    "get_source_access_spec",
    "source_ids",
]
