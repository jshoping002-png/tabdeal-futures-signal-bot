from tabdeal_signal.data_sources import public_api
from tabdeal_signal.data_sources.adapter_catalog import VERIFIED_ADAPTER_BINDINGS
from tabdeal_signal.data_sources.endpoint_contracts import VERIFIED_ENDPOINT_CONTRACTS
from tabdeal_signal.data_sources.operational_manifest import (
    SOURCE_OPERATIONAL_MANIFEST,
    validate_operational_manifest,
)
from tabdeal_signal.data_sources.runtime_config import RUNTIME_CONFIGURED_SOURCE_IDS
from tabdeal_signal.data_sources.source_access import VERIFIED_SOURCE_ACCESS_SPECS


def test_public_api_exports_are_present_and_callable():
    assert public_api.__all__
    for name in public_api.__all__:
        assert hasattr(public_api, name)

    assert public_api.VERIFIED_ADAPTER_BINDINGS is VERIFIED_ADAPTER_BINDINGS
    assert public_api.VERIFIED_ENDPOINT_CONTRACTS is VERIFIED_ENDPOINT_CONTRACTS
    assert public_api.VERIFIED_SOURCE_ACCESS_SPECS is VERIFIED_SOURCE_ACCESS_SPECS
    assert public_api.SOURCE_OPERATIONAL_MANIFEST is SOURCE_OPERATIONAL_MANIFEST


def test_public_api_catalog_sizes_match_existing_operational_state():
    assert len(public_api.VERIFIED_SOURCE_ACCESS_SPECS) == 18
    assert len(public_api.VERIFIED_ADAPTER_BINDINGS) == 24
    assert len(public_api.VERIFIED_ENDPOINT_CONTRACTS) == 27
    assert len(public_api.SOURCE_OPERATIONAL_MANIFEST) == 18


def test_public_api_remains_read_only_and_unactivated():
    counts = public_api.operational_manifest_counts()
    assert counts["live_verified"] == 0
    assert counts["production_ready"] == 0
    assert counts["active"] == 0
    assert all(not spec.strategy_authorized for spec in public_api.VERIFIED_SOURCE_ACCESS_SPECS)
    assert all(not spec.trading_enabled for spec in public_api.VERIFIED_SOURCE_ACCESS_SPECS)


def test_public_api_bindings_cover_manifest_adapters():
    declared = {
        (spec.source_id, class_name)
        for spec in public_api.VERIFIED_SOURCE_ACCESS_SPECS
        for class_name in spec.adapter_classes
    }
    registered = {
        (binding.source_id, binding.class_name)
        for binding in public_api.VERIFIED_ADAPTER_BINDINGS
    }
    assert registered == declared
    assert len(registered) == 24


def test_operational_manifest_cross_catalog_invariants():
    assert validate_operational_manifest() is None
    access_ids = {spec.source_id for spec in public_api.VERIFIED_SOURCE_ACCESS_SPECS}
    manifest_ids = {item.source_id for item in public_api.SOURCE_OPERATIONAL_MANIFEST}
    runtime_ids = set(RUNTIME_CONFIGURED_SOURCE_IDS)
    manifest_runtime_ids = {
        item.source_id
        for item in public_api.SOURCE_OPERATIONAL_MANIFEST
        if item.runtime_configured_count > 0
    }
    assert manifest_ids == access_ids
    assert manifest_runtime_ids == runtime_ids
    assert all(item.reports for item in public_api.SOURCE_OPERATIONAL_MANIFEST)
    assert all(item.endpoint_contract_count > 0 for item in public_api.SOURCE_OPERATIONAL_MANIFEST)
