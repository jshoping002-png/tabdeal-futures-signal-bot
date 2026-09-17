from datetime import datetime, timezone

from tabdeal_signal.data_sources.contracts import DataQualityStatus
from tabdeal_signal.data_sources.deribit_public import DeribitPublicMarketDataSource

UTC = timezone.utc


class FakeTransport:
    def __init__(self, payload, received_at):
        self.payload = payload
        self.received_at = received_at
        self.calls = []

    def post(self, url, method, params, request_id, timeout_seconds):
        self.calls.append((url, method, dict(params), request_id, timeout_seconds))
        return self.payload, self.received_at


def _payload(*ticks):
    count = len(ticks)
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "status": "ok",
            "ticks": list(ticks),
            "open": list(range(count)),
            "high": list(range(count)),
            "low": list(range(count)),
            "close": list(range(count)),
            "volume": list(range(count)),
            "cost": list(range(count)),
        },
    }


def test_chart_filters_only_completed_candles_strictly_before_as_of():
    received = datetime(2026, 1, 1, 0, 31, tzinfo=UTC)
    first = int(datetime(2026, 1, 1, 0, 0, tzinfo=UTC).timestamp() * 1000)
    second = int(datetime(2026, 1, 1, 0, 1, tzinfo=UTC).timestamp() * 1000)
    payload = _payload(first, second)
    source = DeribitPublicMarketDataSource(
        "public/get_tradingview_chart_data",
        params={"instrument_name": "BTC-PERPETUAL", "resolution": "30"},
        transport=FakeTransport(payload, received),
    )
    snapshot = source.fetch_snapshot(as_of=received)
    assert snapshot.metadata.quality is DataQualityStatus.VALID
    assert snapshot.values["result"]["ticks"] == [first]
    assert snapshot.values["result"]["close"] == [0]


def test_chart_exact_close_boundary_is_excluded():
    as_of = datetime(2026, 1, 1, 0, 30, tzinfo=UTC)
    tick = int(datetime(2026, 1, 1, 0, 0, tzinfo=UTC).timestamp() * 1000)
    source = DeribitPublicMarketDataSource(
        "public/get_tradingview_chart_data",
        params={"instrument_name": "BTC-PERPETUAL", "resolution": "30"},
        transport=FakeTransport(_payload(tick), as_of),
    )
    snapshot = source.fetch_snapshot(as_of=as_of)
    assert snapshot.metadata.quality is DataQualityStatus.UNAVAILABLE
    assert snapshot.values["error_class"] == "pit_unavailable"


def test_chart_daily_resolution_fails_closed_for_pit():
    as_of = datetime(2026, 1, 2, tzinfo=UTC)
    tick = int(datetime(2026, 1, 1, tzinfo=UTC).timestamp() * 1000)
    source = DeribitPublicMarketDataSource(
        "public/get_tradingview_chart_data",
        params={"instrument_name": "BTC-PERPETUAL", "resolution": "1D"},
        transport=FakeTransport(_payload(tick), as_of),
    )
    snapshot = source.fetch_snapshot(as_of=as_of)
    assert snapshot.metadata.quality is DataQualityStatus.UNAVAILABLE
    assert snapshot.values["error_class"] == "pit_unavailable"


def test_non_chart_methods_keep_raw_result_behavior():
    received = datetime(2026, 1, 1, tzinfo=UTC)
    payload = {"jsonrpc": "2.0", "id": 1, "result": {"last_price": 123}}
    source = DeribitPublicMarketDataSource(
        "public/ticker",
        params={"instrument_name": "BTC-PERPETUAL"},
        transport=FakeTransport(payload, received),
    )
    snapshot = source.fetch_snapshot(as_of=received)
    assert snapshot.metadata.quality is DataQualityStatus.VALID
    assert snapshot.values["result"] == {"last_price": 123}
