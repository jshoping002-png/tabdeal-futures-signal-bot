from datetime import datetime, timezone

import pytest

from tabdeal_signal.data_sources.contracts import DataQualityStatus
from tabdeal_signal.data_sources.public_sources import PublicHttpResponse
from tabdeal_signal.data_sources.runtime_config import (
    explicit_runtime_endpoint_config,
    runtime_endpoint_config,
)
from tabdeal_signal.data_sources.runtime_source_factory import build_runtime_source

UTC = timezone.utc


class FakeTransport:
    def __init__(self, response):
        self.response = response

    def request(self, method, url, *, query, body, content_type, timeout_seconds):
        return self.response


def response_json():
    return PublicHttpResponse(
        200, datetime(2026, 1, 1, tzinfo=UTC), b'{"ok":1}', "application/json"
    )


def response_text():
    return PublicHttpResponse(
        200, datetime(2026, 1, 1, tzinfo=UTC), b"TEST", "text/plain"
    )


def response_xml():
    return PublicHttpResponse(
        200, datetime(2026, 1, 1, tzinfo=UTC), b"<root />", "application/xml"
    )


@pytest.mark.parametrize(
    ("source_id", "endpoint", "topic"),
    [
        ("binance-spot-market-data", "https://data-api.binance.vision/test", "spot"),
        ("us-treasury-daily-interest-rates", "https://home.treasury.gov/test", "rates"),
        ("sec-edgar-public-api", "https://data.sec.gov/test", "edgar"),
        ("okx-market-data", "https://www.okx.com/test", "market"),
        ("cftc-public-reporting", "https://publicreporting.cftc.gov/test", "cot"),
        ("coinmarketcap-keyless-public-api", "https://pro-api.coinmarketcap.com/test", "market"),
        ("bis-statistics-api", "https://stats.bis.org/test", "stats"),
        ("eurostat-rest-sdmx-api", "https://ec.europa.eu/test", "stats"),
        ("ny-fed-markets-data", "https://markets.newyorkfed.org/test", "markets"),
    ],
)
def test_known_runtime_sources_build_existing_adapters(source_id, endpoint, topic):
    config = runtime_endpoint_config(source_id, endpoint)
    text_sources = {
        "cftc-public-reporting",
        "bis-statistics-api",
        "eurostat-rest-sdmx-api",
        "ny-fed-markets-data",
    }
    if source_id == "us-treasury-daily-interest-rates":
        response = response_xml()
    elif source_id in text_sources:
        response = response_text()
    else:
        response = response_json()
    source = build_runtime_source(
        config,
        topic=topic,
        schema_version="test-v1",
        transport=FakeTransport(response),
    )
    snapshot = source.fetch_snapshot()
    assert snapshot.metadata.quality is DataQualityStatus.VALID
    assert snapshot.metadata.provenance is not None
    assert snapshot.metadata.provenance.source == source_id


def test_coinbase_builds_from_explicit_runtime_scope():
    config = explicit_runtime_endpoint_config(
        "coinbase-advanced-trade-market-data",
        "https://approved.example/test",
        ("approved.example",),
    )
    source = build_runtime_source(
        config,
        topic="market",
        schema_version="test-v1",
        transport=FakeTransport(response_json()),
    )
    assert source.fetch_snapshot().metadata.quality is DataQualityStatus.VALID


def test_factory_rejects_unknown_source_type():
    config = explicit_runtime_endpoint_config(
        "coinbase-advanced-trade-market-data",
        "https://approved.example/test",
        ("approved.example",),
    )
    from tabdeal_signal.data_sources.runtime_config import RuntimeEndpointConfig
    invalid = RuntimeEndpointConfig("not-existing", config.endpoint, config.allowed_hosts)
    with pytest.raises(KeyError):
        build_runtime_source(invalid, topic="x", schema_version="v1")
