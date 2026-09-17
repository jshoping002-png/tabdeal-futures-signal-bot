import pytest

from tabdeal_signal.data_sources.runtime_config import (
    RUNTIME_CONFIGURED_SOURCE_IDS,
    explicit_runtime_endpoint_config,
    runtime_endpoint_config,
)


def test_runtime_configured_source_set_matches_existing_unresolved_catalog():
    assert len(RUNTIME_CONFIGURED_SOURCE_IDS) == 10
    assert set(RUNTIME_CONFIGURED_SOURCE_IDS) == {
        "binance-spot-market-data",
        "us-treasury-daily-interest-rates",
        "sec-edgar-public-api",
        "okx-market-data",
        "coinbase-advanced-trade-market-data",
        "cftc-public-reporting",
        "coinmarketcap-keyless-public-api",
        "bis-statistics-api",
        "eurostat-rest-sdmx-api",
        "ny-fed-markets-data",
    }


@pytest.mark.parametrize(
    ("source_id", "endpoint"),
    [
        ("binance-spot-market-data", "https://data-api.binance.vision/test"),
        ("us-treasury-daily-interest-rates", "https://home.treasury.gov/test"),
        ("sec-edgar-public-api", "https://data.sec.gov/test"),
        ("okx-market-data", "https://www.okx.com/test"),
        ("cftc-public-reporting", "https://publicreporting.cftc.gov/test"),
        ("coinmarketcap-keyless-public-api", "https://pro-api.coinmarketcap.com/test"),
        ("bis-statistics-api", "https://stats.bis.org/test"),
        ("eurostat-rest-sdmx-api", "https://ec.europa.eu/test"),
        ("ny-fed-markets-data", "https://markets.newyorkfed.org/test"),
    ],
)
def test_known_runtime_hosts_accept_https(source_id, endpoint):
    config = runtime_endpoint_config(source_id, endpoint)
    assert config.source_id == source_id
    assert config.endpoint == endpoint


def test_coinbase_requires_explicit_runtime_host_allowlist():
    config = explicit_runtime_endpoint_config(
        "coinbase-advanced-trade-market-data",
        "https://approved.example/test",
        ("approved.example",),
    )
    assert config.source_id == "coinbase-advanced-trade-market-data"


def test_runtime_config_rejects_http_and_out_of_scope_hosts():
    with pytest.raises(ValueError):
        runtime_endpoint_config("sec-edgar-public-api", "http://data.sec.gov/test")
    with pytest.raises(ValueError):
        runtime_endpoint_config("sec-edgar-public-api", "https://example.com/test")


def test_runtime_config_rejects_authentication_material_in_url():
    with pytest.raises(ValueError):
        runtime_endpoint_config(
            "sec-edgar-public-api",
            "https://data.sec.gov/test?api_key=forbidden",
        )


def test_runtime_config_rejects_unknown_or_wrongly_scoped_sources():
    with pytest.raises(KeyError):
        runtime_endpoint_config("not-an-existing-source", "https://example.com/test")
    with pytest.raises(KeyError):
        explicit_runtime_endpoint_config(
            "bybit-futures-market-data",
            "https://api.bybit.com/test",
            ("api.bybit.com",),
        )
