"""Tests for structural validation of the existing runtime endpoint catalog."""

from tabdeal_signal.data_sources.runtime_config import RUNTIME_CONFIGURED_SOURCE_IDS
from tabdeal_signal.data_sources.runtime_config_validation import (
    runtime_configuration_counts,
    validate_runtime_configuration_catalog,
)


def test_runtime_configuration_catalog_is_structurally_valid():
    results = validate_runtime_configuration_catalog()
    assert len(results) == len(RUNTIME_CONFIGURED_SOURCE_IDS) == 10
    assert all(result.valid for result in results)
    assert all(result.runtime_contract_count == 1 for result in results)


def test_runtime_configuration_counts():
    assert runtime_configuration_counts() == {
        "runtime_sources": 10,
        "known_host_sources": 9,
        "explicit_host_sources": 1,
        "runtime_endpoint_contracts": 10,
        "invalid_sources": 0,
    }


def test_only_explicit_host_sources_lack_a_known_runtime_host():
    results = validate_runtime_configuration_catalog()
    explicit = {result.source_id for result in results if result.requires_explicit_host}
    assert explicit == {"coinbase-advanced-trade-market-data"}
