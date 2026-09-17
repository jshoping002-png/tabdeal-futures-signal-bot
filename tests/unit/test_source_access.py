from tabdeal_signal.data_sources.source_access import SourceLifecycle, VERIFIED_SOURCE_ACCESS_SPECS, get_source_access_spec, source_ids


def test_all_existing_verified_source_families_are_ledgered():
    ids = source_ids()
    assert len(ids) == 18
    assert len(set(ids)) == len(ids)
    assert get_source_access_spec("bybit-futures-market-data").reports == ("001", "2040")


def test_only_built_adapters_claim_operational_scope():
    for spec in VERIFIED_SOURCE_ACCESS_SPECS:
        if spec.lifecycle is SourceLifecycle.ADAPTER_BUILT:
            assert spec.adapter_classes
            assert spec.adapter_scope
            assert spec.is_operationally_usable
        else:
            assert not spec.is_operationally_usable


def test_no_source_can_authorize_strategy_or_trading():
    assert all(not spec.strategy_authorized for spec in VERIFIED_SOURCE_ACCESS_SPECS)
    assert all(not spec.trading_enabled for spec in VERIFIED_SOURCE_ACCESS_SPECS)


def test_key_built_sources_reference_existing_adapter_names():
    built_names = {name for spec in VERIFIED_SOURCE_ACCESS_SPECS for name in spec.adapter_classes}
    assert "BinanceCoinMContinuousKlineDataSource" in built_names
    assert "BybitTickersDataSource" in built_names
    assert "BybitInstrumentsInfoDataSource" in built_names
    assert "KrakenFuturesPublicCandleDataSource" in built_names
    assert "DeribitPublicMarketDataSource" in built_names
