import pytest

from tabdeal_signal.data_sources.runtime_config import explicit_runtime_endpoint_config


def test_explicit_runtime_allowlist_cannot_escape_known_source_hosts():
    with pytest.raises(ValueError):
        explicit_runtime_endpoint_config(
            "sec-edgar-public-api",
            "https://example.com/test",
            ("example.com",),
        )


def test_explicit_runtime_allowlist_may_narrow_known_source_hosts():
    config = explicit_runtime_endpoint_config(
        "sec-edgar-public-api",
        "https://data.sec.gov/test",
        ("data.sec.gov",),
    )
    assert config.allowed_hosts == ("data.sec.gov",)


def test_explicit_runtime_allowlist_supports_known_subdomains():
    config = explicit_runtime_endpoint_config(
        "us-treasury-daily-interest-rates",
        "https://home.treasury.gov/test",
        ("home.treasury.gov",),
    )
    assert config.allowed_hosts == ("home.treasury.gov",)


def test_explicit_runtime_allowlist_is_required_for_sources_without_known_hosts():
    config = explicit_runtime_endpoint_config(
        "coinbase-advanced-trade-market-data",
        "https://api.example.test/test",
        ("api.example.test",),
    )
    assert config.allowed_hosts == ("api.example.test",)


def test_runtime_host_values_reject_wildcards_and_paths():
    with pytest.raises(ValueError):
        explicit_runtime_endpoint_config(
            "coinbase-advanced-trade-market-data",
            "https://api.example.test/test",
            ("*.example.test",),
        )
    with pytest.raises(ValueError):
        explicit_runtime_endpoint_config(
            "coinbase-advanced-trade-market-data",
            "https://api.example.test/test",
            ("api.example.test/path",),
        )
