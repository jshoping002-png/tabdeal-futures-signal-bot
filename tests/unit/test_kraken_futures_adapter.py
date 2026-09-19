from datetime import datetime, timezone
from tabdeal_signal.data_sources.kraken_futures import KrakenFuturesPublicCandleDataSource
from tabdeal_signal.data_sources.contracts import DataQualityStatus

UTC = timezone.utc

class FakeTransport:
    def __init__(self, payload, received_at):
        self.payload, self.received_at, self.calls = payload, received_at, []
    def get(self, url, params, timeout_seconds):
        self.calls.append((url, params, timeout_seconds))
        return self.payload, self.received_at

def test_public_candle_path_and_resolution():
    received = datetime(2026,1,1,0,0,0,tzinfo=UTC)
    payload = {"candles": [[1767225600000, "100", "101", "99", "100.5", "10"]], "more_candles": False}
    t = FakeTransport(payload, received)
    s = KrakenFuturesPublicCandleDataSource("trade", "PI_XBTUSD", "1m", transport=t)
    snap = s.fetch_snapshot(as_of=received)
    assert snap.metadata.quality is DataQualityStatus.UNAVAILABLE
    assert snap.values["error_class"] == "pit_unavailable"
    assert t.calls[0][0].endswith("/api/charts/v1/trade/PI_XBTUSD/1m")

def test_closed_candle_is_accepted():
    received = datetime(2026,1,1,0,2,0,tzinfo=UTC)
    opened = int(datetime(2026,1,1,0,0,0,tzinfo=UTC).timestamp()*1000)
    payload = {"candles": [[opened,"100","101","99","100.5","10"]]}
    snap = KrakenFuturesPublicCandleDataSource("trade","PI_XBTUSD","1m",transport=FakeTransport(payload,received)).fetch_snapshot(as_of=received)
    assert snap.metadata.quality is DataQualityStatus.VALID

def test_exact_close_boundary_is_not_closed():
    received = datetime(2026,1,1,0,1,0,tzinfo=UTC)
    opened = int(datetime(2026,1,1,0,0,0,tzinfo=UTC).timestamp()*1000)
    payload = {"candles": [[opened,"100","101","99","100.5","10"]]}
    snap = KrakenFuturesPublicCandleDataSource("trade","PI_XBTUSD","1m",transport=FakeTransport(payload,received)).fetch_snapshot(as_of=received)
    assert snap.metadata.quality is DataQualityStatus.UNAVAILABLE

def test_invalid_resolution_is_rejected():
    try:
        KrakenFuturesPublicCandleDataSource("trade", "PI_XBTUSD", "2m")
    except ValueError:
        pass
    else:
        raise AssertionError("unsupported resolution must be rejected")

def test_future_timestamp_fails_closed():
    received = datetime(2026,1,1,tzinfo=UTC)
    future = int(datetime(2026,1,1,1,0,tzinfo=UTC).timestamp()*1000)
    t = FakeTransport({"candles": [[future,"1","1","1","1","1"]]}, received)
    snap = KrakenFuturesPublicCandleDataSource("trade", "PI_XBTUSD", "1m", transport=t).fetch_snapshot(as_of=received)
    assert snap.metadata.quality is DataQualityStatus.UNAVAILABLE
    assert snap.values["error_class"] == "pit_unavailable"

def test_read_only():
    assert not hasattr(KrakenFuturesPublicCandleDataSource, "place_order")


def test_kraken_redirect_handler_rejects_redirects():
    from tabdeal_signal.data_sources.kraken_futures import _NoRedirectHandler

    assert _NoRedirectHandler().redirect_request(None, None, 302, "Found", {}, "https://attacker.example/") is None
