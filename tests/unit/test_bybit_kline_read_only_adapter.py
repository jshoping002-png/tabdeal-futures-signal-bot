from datetime import datetime, timezone

import pytest

from tabdeal_signal.data.contracts import SnapshotRequest
from tabdeal_signal.data_sources.bybit import JsonTransport
from tabdeal_signal.data_sources.bybit_kline import BybitKlineDataSource

UTC = timezone.utc
REFERENCE = datetime(2026, 1, 1, 2, 0, tzinfo=UTC)


class FakeTransport:
    def __init__(self, payload, received_at=REFERENCE.replace(hour=1, minute=59, second=59)):
        self.payload = payload
        self.received_at = received_at
        self.calls = []

    def get(self, path, params, timeout_seconds):
        self.calls.append((path, params, timeout_seconds))
        return self.payload, self.received_at


ROWS = [
    ["1767225600000", "100", "110", "90", "105", "2", "210"],
    ["1767222000000", "95", "105", "90", "100", "3", "300"],
    ["1767218400000", "90", "100", "85", "95", "4", "380"],
]


def payload(rows=ROWS):
    return {"retCode": 0, "retMsg": "OK", "result": {"symbol": "BTCUSDT", "category": "linear", "list": rows}}


def request():
    return SnapshotRequest(symbols=("BTCUSDT",), timeframes=("60",), reference_time=REFERENCE)


def make_source(payload_value=None):
    return BybitKlineDataSource("btcusdt", transport=FakeTransport(payload_value or payload()))


def test_valid_response_is_pit_safe_and_deterministically_ordered():
    transport = FakeTransport(payload())
    snapshot = BybitKlineDataSource("BTCUSDT", transport=transport).snapshot(request())

    assert [candle.open for candle in snapshot.candles] == [90.0, 95.0, 100.0]
    assert all(candle.close_time < REFERENCE for candle in snapshot.candles)
    assert snapshot.source_id == "bybit-v5-public-kline:linear:BTCUSDT:60"
    assert transport.calls[0][0] == "/v5/market/kline"
    assert transport.calls[0][1]["end"] == str(int(REFERENCE.timestamp() * 1000))
    assert transport.calls[0][1]["interval"] == "60"


def test_response_received_after_reference_time_is_rejected():
    transport = FakeTransport(
        payload(),
        received_at=REFERENCE.replace(hour=2, minute=0, second=1),
    )
    source = BybitKlineDataSource("BTCUSDT", transport=transport)

    with pytest.raises(ValueError, match="received after reference_time"):
        source.snapshot(request())


def test_open_candle_is_excluded_at_exact_close_boundary():
    open_candle = ["1767229200000", "105", "110", "100", "108", "1", "108"]
    snapshot = make_source(payload(ROWS + [open_candle])).snapshot(request())

    assert len(snapshot.candles) == 3
    assert all(candle.close_time < REFERENCE for candle in snapshot.candles)


def test_gap_is_rejected():
    with pytest.raises(ValueError, match="gapped candle series"):
        make_source(payload([ROWS[0], ROWS[2]])).snapshot(request())


def test_duplicate_is_rejected():
    with pytest.raises(ValueError, match="duplicate candles"):
        make_source(payload([ROWS[0], ROWS[0]])).snapshot(request())


def test_response_category_must_match_adapter():
    bad = payload()
    bad["result"]["category"] = "spot"
    with pytest.raises(ValueError, match="response category mismatch"):
        make_source(bad).snapshot(request())


def test_request_scope_must_exactly_match_adapter():
    bad_request = SnapshotRequest(symbols=("ETHUSDT",), timeframes=("60",), reference_time=REFERENCE)
    with pytest.raises(ValueError, match="request scope"):
        make_source().snapshot(bad_request)


def test_bool_retcode_is_rejected():
    bad_payload = {"retCode": True, "result": {"symbol": "BTCUSDT", "list": ROWS}}
    with pytest.raises(ValueError, match="retCode"):
        make_source(bad_payload).snapshot(request())


def test_nonfinite_ohlcv_is_rejected():
    bad_rows = [["1767225600000", "NaN", "110", "90", "105", "2", "210"]]
    with pytest.raises(ValueError, match="finite"):
        make_source(payload(bad_rows)).snapshot(request())


def test_fixed_duration_adapter_rejects_unverified_calendar_intervals():
    with pytest.raises(ValueError, match="fixed-duration"):
        BybitKlineDataSource("BTCUSDT", timeframe="D", transport=FakeTransport(payload()))


def test_unexpected_transport_error_is_not_silenced():
    class BrokenTransport(JsonTransport):
        def get(self, *args, **kwargs):
            raise RuntimeError("programming fault")

    with pytest.raises(RuntimeError, match="programming fault"):
        BybitKlineDataSource("BTCUSDT", transport=BrokenTransport()).snapshot(request())
