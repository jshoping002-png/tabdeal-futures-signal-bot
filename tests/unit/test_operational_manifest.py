import pytest

from tabdeal_signal.data_sources.endpoint_contracts import EndpointExactness
from tabdeal_signal.data_sources.operational_manifest import (
    SOURCE_OPERATIONAL_MANIFEST,
    operational_manifest_counts,
    operational_manifest_for,
)
from tabdeal_signal.data_sources.source_access import SourceLifecycle


def test_manifest_covers_all_existing_source_families_and_no_activation():
    counts = operational_manifest_counts()
    assert counts["source_families"] == 18
    assert counts["adapter_built"] == 18
    assert counts["live_verified"] == 0
    assert counts["production_ready"] == 0
    assert counts["active"] == 0
    assert len(SOURCE_OPERATIONAL_MANIFEST) == 18
    assert all(item.lifecycle is SourceLifecycle.ADAPTER_BUILT for item in SOURCE_OPERATIONAL_MANIFEST)


def test_manifest_endpoint_totals_match_existing_endpoint_catalog():
    counts = operational_manifest_counts()
    assert counts["exact_endpoint_contracts"] == 15
    assert counts["base_path_contracts"] == 2
    assert counts["runtime_configured_contracts"] == 10


def test_manifest_preserves_runtime_requirement_for_base_and_unresolved_sources():
    assert operational_manifest_for("ecb-data-portal-api").runtime_endpoint_required
    assert operational_manifest_for("oecd-data-explorer-sdmx").runtime_endpoint_required
    assert operational_manifest_for("sec-edgar-public-api").runtime_endpoint_required
    assert operational_manifest_for("bybit-futures-market-data").runtime_endpoint_required is False


def test_manifest_reports_endpoint_contract_counts_per_source():
    bybit = operational_manifest_for("bybit-futures-market-data")
    assert bybit.endpoint_contract_count == 6
    assert bybit.exact_endpoint_count == 6
    assert bybit.base_path_count == 0
    assert bybit.runtime_configured_count == 0


def test_manifest_lookup_rejects_unknown_source():
    with pytest.raises(KeyError):
        operational_manifest_for("not-an-existing-source")
