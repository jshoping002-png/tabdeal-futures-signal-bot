"""Tests for structural validation of the existing endpoint catalog."""

from tabdeal_signal.data_sources.endpoint_contract_validation import (
    endpoint_catalog_counts,
    validate_endpoint_catalog,
)


def test_full_endpoint_catalog_is_structurally_valid():
    results = validate_endpoint_catalog()
    assert len(results) == 18
    assert all(result.valid for result in results)
    assert all(result.contract_count > 0 for result in results)


def test_endpoint_catalog_counts():
    assert endpoint_catalog_counts() == {
        "source_families": 18,
        "contracts": 27,
        "exact": 15,
        "base_path": 2,
        "runtime_configured": 10,
        "invalid_source_families": 0,
    }
