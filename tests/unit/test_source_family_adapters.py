from datetime import datetime, timedelta, timezone
import json

import pytest

from tabdeal_signal.data_sources.contracts import DataQualityStatus
from tabdeal_signal.data_sources.public_sources import PublicHttpResponse
from tabdeal_signal.data_sources.source_family_adapters import (
    BinanceSpotMarketDataSource,
    CoinbaseAdvancedTradeMarketDataSource,
    NyFedMarketsDataSource,
    OecdSdmxDataSource,
    OkxMarketDataSource,
)

UTC = timezone.utc
RECEIVED = datetime(2026, 1, 1, tzinfo=UTC)


class FakeTransport:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def request(self, method, url, *, query, body, content_type, timeout_seconds):
        self.calls.append((method, url, query, body, content_type, timeout_seconds))
        return self.response


def http_response(body: bytes, *, content_type: str = "application/json", status: int = 200) -> PublicHttpResponse:
    return PublicHttpResponse(status, RECEIVED, body, content_type)


@pytest.mark.parametrize(
    "factory, expected_source, expected_endpoint, expected_body_type",
    [
        (
            lambda transport: BinanceSpotMarketDataSource(
                endpoint="https://data-api.binance.vision/test",
                topic="spot-market",
                schema_version="v1",
                transport=transport,
            ),
            "binance-spot-market-data",
            "https://data-api.binance.vision/test",
            "json",
        ),
        (
            lambda transport: OkxMarketDataSource(
                endpoint="https://www.okx.com/test",
                topic="market",
                schema_version="v1",
                transport=transport,
            ),
            "okx-market-data",
            "https://www.okx.com/test",
            "json",
        ),
        (
            lambda transport: CoinbaseAdvancedTradeMarketDataSource(
                endpoint="https://runtime.example/test",
                topic="market",
                schema_version="v1",
                allowed_hosts=("runtime.example",),
                transport=transport,
            ),
            "coinbase-advanced-trade-market-data",
            "https://runtime.example/test",
            "json",
        ),
        (
            lambda transport: OecdSdmxDataSource(
                endpoint="https://sdmx.oecd.org/test",
                topic="dataset",
                schema_version="v1",
                transport=transport,
            ),
            "oecd-data-explorer-sdmx",
            "https://sdmx.oecd.org/test",
            "text",
        ),
        (
            lambda transport: NyFedMarketsDataSource(
                endpoint="https://markets.newyorkfed.org/test",
                topic="markets",
                schema_version="v1",
                transport=transport,
            ),
            "ny-fed-markets-data",
            "https://markets.newyorkfed.org/test",
            "text",
        ),
    ],
)
def test_new_source_family_adapter_is_public_and_preserves_canonical_identity(
    factory, expected_source, expected_endpoint, expected_body_type
):
    body = b'{"ok":1}' if expected_body_type == "json" else b"SDMX-TEST"
    content_type = "application/json" if expected_body_type == "json" else "text/plain"
    transport = FakeTransport(http_response(body, content_type=content_type))
    source = factory(transport)

    snapshot = source.fetch_snapshot()

    assert snapshot.metadata.quality is DataQualityStatus.VALID
    assert snapshot.metadata.provenance is not None
    assert snapshot.metadata.provenance.source == expected_source
    assert snapshot.metadata.provenance.reference == expected_endpoint
    assert transport.calls[0][0] == "GET"
    assert transport.calls[0][1] == expected_endpoint
    if expected_body_type == "json":
        assert snapshot.values["payload"] == {"ok": 1}
    else:
        assert snapshot.values["text"] == "SDMX-TEST"


@pytest.mark.parametrize(
    "factory",
    [
        lambda transport: BinanceSpotMarketDataSource(
            endpoint="https://data-api.binance.vision/test", topic="spot", schema_version="v1", transport=transport
        ),
        lambda transport: OkxMarketDataSource(
            endpoint="https://www.okx.com/test", topic="market", schema_version="v1", transport=transport
        ),
        lambda transport: CoinbaseAdvancedTradeMarketDataSource(
            endpoint="https://runtime.example/test", topic="market", schema_version="v1",
            allowed_hosts=("runtime.example",), transport=transport
        ),
        lambda transport: OecdSdmxDataSource(
            endpoint="https://sdmx.oecd.org/test", topic="dataset", schema_version="v1", transport=transport
        ),
        lambda transport: NyFedMarketsDataSource(
            endpoint="https://markets.newyorkfed.org/test", topic="markets", schema_version="v1", transport=transport
        ),
    ],
)
def test_new_source_family_adapters_are_point_in_time_safe(factory):
    received = RECEIVED + timedelta(seconds=2)
    transport = FakeTransport(http_response(b"{}", status=200))
    transport.response = PublicHttpResponse(200, received, b"{}", "application/json")
    source = factory(transport)

    snapshot = source.fetch_snapshot(as_of=RECEIVED)

    assert snapshot.metadata.quality is DataQualityStatus.UNAVAILABLE
    assert snapshot.values["error_class"] == "pit_unavailable"


def test_new_source_family_adapter_rejects_auth_query_material():
    with pytest.raises(ValueError):
        BinanceSpotMarketDataSource(
            endpoint="https://data-api.binance.vision/test",
            topic="spot",
            schema_version="v1",
            query={"api_key": "forbidden"},
        )
