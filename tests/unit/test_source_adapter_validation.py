"""Tests for structural validation of the existing adapter catalog."""

from tabdeal_signal.data_sources.source_adapter_validation import (
    source_adapter_validation_counts,
    validate_source_adapter_catalog,
)


def test_full_source_adapter_catalog_is_structurally_valid():
    results = validate_source_adapter_catalog()
    assert len(results) == 18
    assert all(result.valid for result in results)
    assert all(result.declared_adapter_count == result.resolved_adapter_count for result in results)


def test_source_adapter_validation_counts():
    assert source_adapter_validation_counts() == {
        "source_families": 18,
        "valid_source_families": 18,
        "adapter_bindings": 24,
        "resolved_adapters": 24,
        "invalid_source_families": 0,
    }
