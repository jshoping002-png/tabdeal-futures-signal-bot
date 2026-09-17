from tabdeal_signal.data_sources.adapter_catalog import (
    VERIFIED_ADAPTER_BINDINGS,
    adapter_bindings_for,
    resolve_adapter_class,
    source_ids_with_adapters,
)
from tabdeal_signal.data_sources.source_access import VERIFIED_SOURCE_ACCESS_SPECS, source_ids


def test_catalog_covers_every_adapter_declared_by_source_access():
    declared = {
        (spec.source_id, class_name)
        for spec in VERIFIED_SOURCE_ACCESS_SPECS
        for class_name in spec.adapter_classes
    }
    registered = {(item.source_id, item.class_name) for item in VERIFIED_ADAPTER_BINDINGS}
    assert registered == declared
    assert len(VERIFIED_ADAPTER_BINDINGS) == 24


def test_catalog_covers_all_existing_source_families():
    assert set(source_ids_with_adapters()) == set(source_ids())
    assert len(source_ids_with_adapters()) == 18


def test_bybit_bindings_are_split_by_concrete_modules():
    assert adapter_bindings_for("bybit-futures-market-data")
    modules = {item.module_path for item in adapter_bindings_for("bybit-futures-market-data")}
    assert modules == {
        ".bybit_kline",
        ".bybit",
        ".bybit_open_interest",
        ".bybit_funding",
        ".bybit_tickers",
        ".bybit_instruments",
    }


def test_runtime_resolution_rejects_unknown_bindings():
    import pytest

    with pytest.raises(KeyError):
        resolve_adapter_class("bybit-futures-market-data", "UnknownDataSource")
