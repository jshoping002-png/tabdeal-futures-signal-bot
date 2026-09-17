from importlib import import_module

import pytest

from tabdeal_signal.data_sources.source_access import (
    SourceAccessSpec,
    SourceLifecycle,
    VERIFIED_SOURCE_ACCESS_SPECS,
    get_source_access_spec,
    source_ids,
)


ADAPTER_MODULES = {
    "BinanceCoinMContinuousKlineDataSource": "tabdeal_signal.data_sources.binance_coinm",
    "BybitKlineDataSource": "tabdeal_signal.data_sources.bybit_kline",
    "BybitOrderbookDataSource": "tabdeal_signal.data_sources.bybit",
    "BybitOpenInterestDataSource": "tabdeal_signal.data_sources.bybit_open_interest",
    "BybitFundingRateDataSource": "tabdeal_signal.data_sources.bybit_funding",
    "BybitTickersDataSource": "tabdeal_signal.data_sources.bybit_tickers",
    "BybitInstrumentsInfoDataSource": "tabdeal_signal.data_sources.bybit_instruments",
    "BlsPublicApiDataSource": "tabdeal_signal.data_sources.public_sources",
    "BinanceSpotMarketDataSource": "tabdeal_signal.data_sources.source_family_adapters",
    "TreasuryDailyRatesDataSource": "tabdeal_signal.data_sources.public_sources",
    "SecEdgarDataSource": "tabdeal_signal.data_sources.public_sources",
    "OkxMarketDataSource": "tabdeal_signal.data_sources.source_family_adapters",
    "KrakenFuturesPublicCandleDataSource": "tabdeal_signal.data_sources.kraken_futures",
    "CoinbaseAdvancedTradeMarketDataSource": "tabdeal_signal.data_sources.source_family_adapters",
    "DeribitPublicMarketDataSource": "tabdeal_signal.data_sources.deribit_public",
    "CftcPublicReportingDataSource": "tabdeal_signal.data_sources.public_sources",
    "CoinMarketCapKeylessDataSource": "tabdeal_signal.data_sources.public_sources",
    "EcbSdmxDataSource": "tabdeal_signal.data_sources.public_sources",
    "BisStatisticsDataSource": "tabdeal_signal.data_sources.public_sources",
    "EurostatDataSource": "tabdeal_signal.data_sources.public_sources",
    "OecdSdmxDataSource": "tabdeal_signal.data_sources.source_family_adapters",
    "NyFedMarketsDataSource": "tabdeal_signal.data_sources.source_family_adapters",
}

EXPECTED_SOURCE_IDS = {
    "binance-futures-market-data", "bybit-futures-market-data", "bls-public-api",
    "binance-spot-market-data", "bybit-spot-market-data", "us-treasury-daily-interest-rates",
    "sec-edgar-public-api", "okx-market-data", "kraken-futures-market-data",
    "coinbase-advanced-trade-market-data", "deribit-market-data", "cftc-public-reporting",
    "coinmarketcap-keyless-public-api", "ecb-data-portal-api", "bis-statistics-api",
    "eurostat-rest-sdmx-api", "oecd-data-explorer-sdmx", "ny-fed-markets-data",
}


def test_catalog_has_exactly_the_registered_source_families():
    assert set(source_ids()) == EXPECTED_SOURCE_IDS
    assert len(VERIFIED_SOURCE_ACCESS_SPECS) == 18
    assert len(set(source_ids())) == 18


def test_every_registered_adapter_class_is_importable_and_built():
    seen_classes = set()
    for spec in VERIFIED_SOURCE_ACCESS_SPECS:
        assert spec.lifecycle is SourceLifecycle.ADAPTER_BUILT
        assert spec.strategy_authorized is False
        assert spec.trading_enabled is False
        for class_name in spec.adapter_classes:
            module = import_module(ADAPTER_MODULES[class_name])
            assert getattr(module, class_name) is not None
            seen_classes.add(class_name)
    assert seen_classes == set(ADAPTER_MODULES)


def test_existing_report_linkage_is_preserved():
    for report in ("001", "002", "003", "004", "005", "006", "007", "008"):
        assert [spec for spec in VERIFIED_SOURCE_ACCESS_SPECS if report in spec.reports]
    assert "2040" in get_source_access_spec("bybit-futures-market-data").reports


def test_unresolved_runtime_endpoints_remain_explicit():
    for source_id in (
        "binance-spot-market-data",
        "okx-market-data",
        "coinbase-advanced-trade-market-data",
        "oecd-data-explorer-sdmx",
        "ny-fed-markets-data",
    ):
        spec = get_source_access_spec(source_id)
        assert spec.exact_endpoint_required is True
        assert spec.lifecycle is SourceLifecycle.ADAPTER_BUILT
        assert any("runtime-configured" in scope for scope in spec.adapter_scope)


def make_spec(lifecycle, *, adapter_classes=("Adapter",), adapter_scope=("scope",), verified_hosts=("example.com",)):
    return SourceAccessSpec(
        source_id="test-source",
        name="Test Source",
        reports=("001",),
        lifecycle=lifecycle,
        adapter_classes=adapter_classes,
        adapter_scope=adapter_scope,
        verified_hosts=verified_hosts,
    )


def test_lifecycle_rank_is_monotonic():
    ordered = tuple(SourceLifecycle)
    assert [item.rank for item in ordered] == list(range(len(ordered)))


@pytest.mark.parametrize("lifecycle", tuple(SourceLifecycle))
def test_operational_usability_requires_adapter_contract(lifecycle):
    spec = make_spec(lifecycle)
    expected = lifecycle.rank >= SourceLifecycle.ADAPTER_BUILT.rank
    assert spec.is_operationally_usable is expected


def test_adapter_built_or_later_requires_adapter_classes_and_scope():
    for lifecycle in (
        SourceLifecycle.ADAPTER_BUILT,
        SourceLifecycle.LIVE_VERIFIED,
        SourceLifecycle.PRODUCTION_READY,
        SourceLifecycle.ACTIVE,
    ):
        with pytest.raises(ValueError):
            make_spec(lifecycle, adapter_classes=(), adapter_scope=("scope",))
        with pytest.raises(ValueError):
            make_spec(lifecycle, adapter_classes=("Adapter",), adapter_scope=())


def test_live_verified_or_later_requires_verified_hosts():
    for lifecycle in (
        SourceLifecycle.LIVE_VERIFIED,
        SourceLifecycle.PRODUCTION_READY,
        SourceLifecycle.ACTIVE,
    ):
        with pytest.raises(ValueError):
            make_spec(lifecycle, verified_hosts=())


def test_documented_and_access_configured_can_be_metadata_only():
    for lifecycle in (SourceLifecycle.DOCUMENTED, SourceLifecycle.ACCESS_CONFIGURED):
        spec = make_spec(lifecycle, adapter_classes=(), adapter_scope=(), verified_hosts=())
        assert not spec.is_operationally_usable


def test_current_verified_source_families_remain_adapter_usable():
    assert len(VERIFIED_SOURCE_ACCESS_SPECS) == 18
    assert all(spec.lifecycle is SourceLifecycle.ADAPTER_BUILT for spec in VERIFIED_SOURCE_ACCESS_SPECS)
    assert all(spec.is_operationally_usable for spec in VERIFIED_SOURCE_ACCESS_SPECS)
