"""Tests for deterministic source readiness gates."""

import pytest

from tabdeal_signal.data_sources.operational_manifest import operational_manifest_counts
from tabdeal_signal.data_sources.source_access import SourceLifecycle
from tabdeal_signal.data_sources.source_readiness import (
    ReadinessGate,
    all_source_readiness,
    source_readiness_counts,
    source_readiness_for,
)


ENDPOINT_CONFIGURATION_SOURCE_IDS = (
    "binance-spot-market-data",
    "us-treasury-daily-interest-rates",
    "sec-edgar-public-api",
    "okx-market-data",
    "coinbase-advanced-trade-market-data",
    "cftc-public-reporting",
    "coinmarketcap-keyless-public-api",
    "ecb-data-portal-api",
    "bis-statistics-api",
    "eurostat-rest-sdmx-api",
    "oecd-data-explorer-sdmx",
    "ny-fed-markets-data",
)


LIVE_VERIFICATION_SOURCE_IDS = (
    "binance-futures-market-data",
    "bybit-futures-market-data",
    "bls-public-api",
    "bybit-spot-market-data",
    "kraken-futures-market-data",
    "deribit-market-data",
)


def test_current_source_readiness_counts_are_explicit():
    assert source_readiness_counts() == {
        ReadinessGate.ADAPTER_BUILD.value: 0,
        ReadinessGate.ENDPOINT_CONFIGURATION.value: 12,
        ReadinessGate.LIVE_VERIFICATION.value: 6,
        ReadinessGate.PRODUCTION_VALIDATION.value: 0,
        ReadinessGate.ACTIVATION.value: 0,
        ReadinessGate.COMPLETE.value: 0,
    }
    assert len(all_source_readiness()) == operational_manifest_counts()["source_families"] == 18


def test_endpoint_configuration_is_the_next_gate_for_unresolved_endpoints():
    for source_id in ENDPOINT_CONFIGURATION_SOURCE_IDS:
        readiness = source_readiness_for(source_id)
        assert readiness.lifecycle is SourceLifecycle.ADAPTER_BUILT
        assert readiness.gate is ReadinessGate.ENDPOINT_CONFIGURATION
        assert readiness.blocked
        assert readiness.blockers == ("endpoint_contract_resolution",)


def test_exact_endpoint_sources_stop_at_live_verification():
    for source_id in LIVE_VERIFICATION_SOURCE_IDS:
        readiness = source_readiness_for(source_id)
        assert readiness.lifecycle is SourceLifecycle.ADAPTER_BUILT
        assert readiness.gate is ReadinessGate.LIVE_VERIFICATION
        assert readiness.blockers == ("live_operational_verification",)


def test_all_current_sources_are_partitioned_once_by_next_gate():
    readiness = all_source_readiness()
    assert {item.source_id for item in readiness} == {
        "binance-futures-market-data",
        "bybit-futures-market-data",
        "bls-public-api",
        "binance-spot-market-data",
        "bybit-spot-market-data",
        "us-treasury-daily-interest-rates",
        "sec-edgar-public-api",
        "okx-market-data",
        "kraken-futures-market-data",
        "coinbase-advanced-trade-market-data",
        "deribit-market-data",
        "cftc-public-reporting",
        "coinmarketcap-keyless-public-api",
        "ecb-data-portal-api",
        "bis-statistics-api",
        "eurostat-rest-sdmx-api",
        "oecd-data-explorer-sdmx",
        "ny-fed-markets-data",
    }
    assert sum(not item.blocked for item in readiness) == 0


def test_unknown_source_is_rejected():
    with pytest.raises(KeyError):
        source_readiness_for("not-a-registered-source")
