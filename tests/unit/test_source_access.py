from tabdeal_signal.data_sources import (
    SourceLifecycle,
    VERIFIED_SOURCE_ACCESS_SPECS,
    get_source_access_spec,
    source_ids,
)


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


def test_bybit_adapter_scope_is_explicit_and_read_only():
    spec = get_source_access_spec("bybit-futures-market-data")
    assert spec.lifecycle is SourceLifecycle.ADAPTER_BUILT
    assert "public REST kline" in spec.adapter_scope
    assert "public REST orderbook" in spec.adapter_scope
    assert spec.verified_hosts


def test_unknown_source_is_rejected():
    try:
        get_source_access_spec("unknown")
    except KeyError:
        pass
    else:
        raise AssertionError("unknown source id must raise KeyError")
