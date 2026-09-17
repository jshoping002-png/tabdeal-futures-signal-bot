from datetime import datetime, timezone
import json

from tabdeal_signal.data_sources.contracts import DataQualityStatus
from tabdeal_signal.data_sources.source_family_adapters import (
    BinanceSpotMarketDataSource,
    CoinbaseAdvancedTradeMarketDataSource,
    NyFedMarketsDataSource,
    OecdSdmxDataSource,
    OkxMarketDataSource,
)
from tabdeal_signal.data_sources.public_sources import PublicHttpResponse

UTC = timezone.utc
WHEN = datetime(2026, 1, 1, tzinfo=UTC)


class FakeTransport:
    def __init__(self, body=b"{}"):
        self.body = body
        self.calls = []

    def request(self, method, url, *, query, body, content_type, timeout_seconds):
        self.calls.append((method, url, query, body, content_type, timeout_seconds))
        return PublicHttpResponse(200, WHEN, self.body, "application/json")


def test_remaining_source_wrappers_preserve_public_boundary_and_payload():
    cases = [
        (
            BinanceSpotMarketDataSource,
            "https://data-api.binance.vision/api/test",
            "spot",
            "EXCHANGE",
        ),
        (
            OkxMarketDataSource,
            "https://www.okx.com/api/v5/test",
            "market",
            "EXCHANGE",
        ),
        (
            OecdSdmxDataSource,
            "https://sdmx.oecd.org/public/rest/test",
            "series",
            "MACRO",
        ),
        (
            NyFedMarketsDataSource,
            "https://markets.newyorkfed.org/api/test",
            "markets",
            "MACRO",
        ),
    ]
    for cls, endpoint, topic, kind in cases:
        transport = FakeTransport(json.dumps({"ok": True}).encode())
        source = cls(
            endpoint=endpoint,
            topic=topic,
            schema_version="reports-001-2040",
            transport=transport,
        )
        snapshot = source.fetch_snapshot()
        assert snapshot.metadata.quality is DataQualityStatus.VALID
        assert snapshot.metadata.source_kind.value == kind.lower()
        assert transport.calls[0][0] == "GET"
        assert snapshot.metadata.provenance is not None
        assert snapshot.metadata.provenance.source == source.source_id


def test_coinbase_requires_explicit_approved_api_host():
    transport = FakeTransport(json.dumps({"ok": True}).encode())
    source = CoinbaseAdvancedTradeMarketDataSource(
        endpoint="https://api.example.test/test",
        topic="products",
        schema_version="reports-001-2040",
        allowed_hosts=("api.example.test",),
        transport=transport,
    )
    snapshot = source.fetch_snapshot()
    assert snapshot.metadata.quality is DataQualityStatus.VALID
    assert snapshot.metadata.provenance is not None
    assert snapshot.metadata.provenance.source == "coinbase-advanced-trade-market-data"


def test_coinbase_host_must_be_explicitly_allowed():
    try:
        CoinbaseAdvancedTradeMarketDataSource(
            endpoint="https://api.example.test/test",
            topic="products",
            schema_version="reports-001-2040",
            allowed_hosts=("different.example.test",),
        )
    except ValueError as exc:
        assert "host is not allowed" in str(exc)
    else:
        raise AssertionError("unexpectedly accepted unapproved Coinbase host")
