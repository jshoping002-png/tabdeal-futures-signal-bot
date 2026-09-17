from datetime import datetime, timezone

from tabdeal_signal.data_sources.bybit_instruments import BybitInstrumentsInfoDataSource
from tabdeal_signal.data_sources.bybit_tickers import BybitTickersDataSource
from tabdeal_signal.data_sources.contracts import DataQualityStatus

UTC = timezone.utc


class FakeTransport:
    def __init__(self, payload, received_at):
        self.payload = payload
        self.received_at = received_at
        self.calls = []

    def get(self, path, params, timeout_seconds):
        self.calls.append((path, dict(params), timeout_seconds))
        return self.payload, self.received_at


def test_tickers_normalizes_linear_snapshot_and_pit():
    received = datetime(2026, 1, 1, tzinfo=UTC)
    transport = FakeTransport({"retCode": 0, "result": {"category": "linear", "list": [{"symbol": "BTCUSDT", "lastPrice": "100.10", "markPrice": "100.20", "fundingRate": "0.0001", "openInterest": "12.5"}]}}, received)
    source = BybitTickersDataSource(category="linear", symbol="BTCUSDT", transport=transport)
    snapshot = source.fetch_snapshot(as_of=received)
    assert snapshot.metadata.quality is DataQualityStatus.VALID
    assert snapshot.values["rows"][0]["lastPrice"] == "100.10"
    assert transport.calls[0][0] == "/v5/market/tickers"


def test_option_tickers_require_symbol_or_base_coin():
    try:
        BybitTickersDataSource(category="option")
    except ValueError:
        pass
    else:
        raise AssertionError("option ticker query must be scoped")


def test_instruments_info_normalizes_page_and_cursor():
    received = datetime(2026, 1, 1, tzinfo=UTC)
    transport = FakeTransport({"retCode": 0, "result": {"category": "linear", "nextPageCursor": "next", "list": [{"symbol": "BTCUSDT", "status": "Trading", "launchTime": "1700000000000", "deliveryTime": "0", "priceScale": "2", "priceFilter": {"tickSize": "0.10"}, "lotSizeFilter": {"minOrderQty": "0.001", "qtyStep": "0.001"}}]}}, received)
    source = BybitInstrumentsInfoDataSource(category="linear", transport=transport)
    snapshot = source.fetch_snapshot(as_of=received)
    assert snapshot.metadata.quality is DataQualityStatus.VALID
    assert snapshot.values["next_page_cursor"] == "next"
    assert snapshot.values["rows"][0]["symbol"] == "BTCUSDT"
    assert transport.calls[0][1]["limit"] == "500"


def test_spot_instruments_info_does_not_send_pagination_params():
    received = datetime(2026, 1, 1, tzinfo=UTC)
    transport = FakeTransport({"retCode": 0, "result": {"category": "spot", "list": [{"symbol": "BTCUSDT", "status": "Trading"}]}}, received)
    snapshot = BybitInstrumentsInfoDataSource(category="spot", transport=transport).fetch_snapshot(as_of=received)
    assert snapshot.metadata.quality is DataQualityStatus.VALID
    assert "limit" not in transport.calls[0][1]
    assert "cursor" not in transport.calls[0][1]


def test_spot_instruments_info_rejects_cursor_or_limit():
    try:
        BybitInstrumentsInfoDataSource(category="spot", cursor="x")
    except ValueError:
        pass
    else:
        raise AssertionError("spot cursor must be rejected")
    try:
        BybitInstrumentsInfoDataSource(category="spot", limit=500)
    except ValueError:
        pass
    else:
        raise AssertionError("spot limit must be rejected")


def test_catalog_adapters_are_read_only():
    assert not hasattr(BybitTickersDataSource, "place_order")
    assert not hasattr(BybitInstrumentsInfoDataSource, "place_order")
