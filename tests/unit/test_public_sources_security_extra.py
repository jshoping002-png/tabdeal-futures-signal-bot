"""Additional no-credential transport boundary tests."""

import pytest

from tabdeal_signal.data_sources.public_sources import UrllibPublicHttpTransport


def test_transport_rejects_auth_material_already_present_in_url():
    transport = UrllibPublicHttpTransport()
    for key in ("api_key", "apikey", "api-key", "secret", "signature", "access_token", "authorization", "bearer"):
        with pytest.raises(ValueError):
            transport.request(
                "GET",
                f"https://data.sec.gov/test?{key}=value",
                query=None,
                body=None,
                content_type=None,
                timeout_seconds=1,
            )


def test_transport_rejects_auth_material_in_query_mapping():
    transport = UrllibPublicHttpTransport()
    for key in ("api_key", "secret", "authorization"):
        with pytest.raises(ValueError):
            transport.request(
                "GET",
                "https://data.sec.gov/test",
                query={key: "value"},
                body=None,
                content_type=None,
                timeout_seconds=1,
            )


def test_transport_rejects_auth_material_nested_in_query_values():
    transport = UrllibPublicHttpTransport()
    with pytest.raises(ValueError):
        transport.request(
            "GET",
            "https://data.sec.gov/test",
            query={"filters": {"authorization": "value"}},
            body=None,
            content_type=None,
            timeout_seconds=1,
        )


def test_transport_rejects_non_https_public_endpoint():
    transport = UrllibPublicHttpTransport()
    with pytest.raises(ValueError):
        transport.request(
            "GET",
            "http://data.sec.gov/test",
            query=None,
            body=None,
            content_type=None,
            timeout_seconds=1,
        )
