from datetime import datetime, timezone
from tabdeal_signal.data_sources.deribit_public import DeribitPublicMarketDataSource
from tabdeal_signal.data_sources.contracts import DataQualityStatus

UTC = timezone.utc

class FakeTransport:
    def __init__(self, response, received_at):
        self.response, self.received_at, self.calls = response, received_at, []
    def post(self, url, method, params, request_id, timeout_seconds):
        self.calls.append((url, method, dict(params), request_id, timeout_seconds))
        return self.response, self.received_at

def test_public_method_allowlist_and_raw_result():
    received = datetime(2026,1,1,tzinfo=UTC)
    t = FakeTransport({"jsonrpc":"2.0","id":1,"result":{"instrument_name":"BTC-PERPETUAL"}}, received)
    s = DeribitPublicMarketDataSource("public/ticker", params={"instrument_name":"BTC-PERPETUAL"}, transport=t)
    snap = s.fetch_snapshot(as_of=received)
    assert snap.metadata.quality is DataQualityStatus.VALID
    assert snap.values["result"]["instrument_name"] == "BTC-PERPETUAL"
    assert t.calls[0][1] == "public/ticker"
    assert t.calls[0][0].endswith("/api/v2/")

def test_private_method_is_rejected():
    try:
        DeribitPublicMarketDataSource("private/get_positions")
    except ValueError:
        pass
    else:
        raise AssertionError("private Deribit methods must be rejected")

def test_rpc_error_fails_closed():
    received = datetime(2026,1,1,tzinfo=UTC)
    t = FakeTransport({"jsonrpc":"2.0","id":1,"error":{"code":10001,"message":"bad"}}, received)
    snap = DeribitPublicMarketDataSource("public/ticker", transport=t).fetch_snapshot(as_of=received)
    assert snap.metadata.quality is DataQualityStatus.UNAVAILABLE
    assert snap.values["error_class"] == "provider_error"

def test_read_only():
    assert not hasattr(DeribitPublicMarketDataSource, "place_order")
