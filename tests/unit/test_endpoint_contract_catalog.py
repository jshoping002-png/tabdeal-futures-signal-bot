from tabdeal_signal.data_sources.endpoint_contracts import (
    EndpointExactness,
    VERIFIED_ENDPOINT_CONTRACTS,
    endpoint_contracts_for,
    source_ids_with_endpoint_contracts,
)
from tabdeal_signal.data_sources.source_access import VERIFIED_SOURCE_ACCESS_SPECS, source_ids


def test_contract_catalog_has_expected_shape():
    assert len(VERIFIED_ENDPOINT_CONTRACTS) == 27
    assert sum(item.exactness is EndpointExactness.EXACT for item in VERIFIED_ENDPOINT_CONTRACTS) == 15
    assert sum(item.exactness is EndpointExactness.BASE_PATH for item in VERIFIED_ENDPOINT_CONTRACTS) == 2
    assert sum(item.exactness is EndpointExactness.RUNTIME_CONFIGURED for item in VERIFIED_ENDPOINT_CONTRACTS) == 10
    assert all(item.auth_required is False for item in VERIFIED_ENDPOINT_CONTRACTS)


def test_every_existing_source_family_has_endpoint_contract():
    assert set(source_ids_with_endpoint_contracts()) == set(source_ids())
    assert len(source_ids_with_endpoint_contracts()) == 18


def test_evidence_links_remain_inside_existing_reports():
    allowed = {"001", "002", "003", "004", "005", "006", "007", "008", "2040"}
    assert all(item.evidence_report in allowed for item in VERIFIED_ENDPOINT_CONTRACTS)


def test_known_exact_paths_are_not_blank():
    exact = [item for item in VERIFIED_ENDPOINT_CONTRACTS if item.exactness is EndpointExactness.EXACT]
    assert all(item.path for item in exact)
    assert endpoint_contracts_for("bybit-futures-market-data")


def test_runtime_configured_items_do_not_invent_paths():
    unresolved = (
        "binance-spot-market-data", "us-treasury-daily-interest-rates", "sec-edgar-public-api",
        "okx-market-data", "coinbase-advanced-trade-market-data", "cftc-public-reporting",
        "coinmarketcap-keyless-public-api", "bis-statistics-api", "eurostat-rest-sdmx-api",
        "ny-fed-markets-data",
    )
    for source_id in unresolved:
        contracts = endpoint_contracts_for(source_id)
        assert contracts
        assert all(item.exactness is EndpointExactness.RUNTIME_CONFIGURED for item in contracts)
        assert all(item.path is None for item in contracts)


def test_report_linkage_is_preserved():
    reports = {report for spec in VERIFIED_SOURCE_ACCESS_SPECS for report in spec.reports}
    assert {"001", "002", "003", "004", "005", "006", "007", "008"}.issubset(reports)
    assert "2040" in reports
