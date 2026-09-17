from datetime import datetime, timezone

from tabdeal_signal.data_sources.binance_coinm import BinanceCoinMContinuousKlineDataSource
from tabdeal_signal.data_sources.contracts import DataQualityStatus

UTC = timezone.utc


class FakeTransport:
    def __init__(self, payload, received_at):
        self.payload = payload
        self.received_at = received_at
        self.calls = []

    def get(self, url, params, timeout_seconds):
        self.calls.append((url, dict(params), timeout_seconds))
        return self.payload, self.received_at


def test_continuous_kline_uses_documented_path_and_preserves_rows():
    received = datetime(2026, 1, 1, tzinfo=UTC)
    payload = [[1767225300000, "100", "101", "99", "100.5", "12", 1767225599999, "1200", 4, "6", "600", "0"]]
    transport = FakeTransport(payload, received)
    source = BinanceCoinMContinuousKlineDataSource("btcusd", "PERPETUAL", "1m", transport=transport)
    snapshot = source.fetch_snapshot(as_of=received)
    assert snapshot.metadata.quality is DataQualityStatus.VALID
    assert snapshot.values["rows"][0][0] == 1767225300000
    assert transport.calls[0][0].endswith("/dapi/v1/continuousKlines")
    assert transport.calls[0][1]["pair"] == "BTCUSD"
    assert transport.calls[0][1]["contractType"] == "PERPETUAL"


def test_future_closing_candle_is_pit_unavailable():
    received = datetime(2026, 1, 1, tzinfo=UTC)
    future_close = int(datetime(2026, 1, 1, 0, 1, tzinfo=UTC).timestamp() * 1000)
    payload = [[1767225600000, "1", "1", "1", "1", "1", future_close, "1", 1, "1", "1", "0"]]
    source = BinanceCoinMContinuousKlineDataSource("BTCUSD", "PERPETUAL", "1m", transport=FakeTransport(payload, received))
    snapshot = source.fetch_snapshot(as_of=received)
    assert snapshot.metadata.quality is DataQualityStatus.UNAVAILABLE
    assert snapshot.values["error_class"] == "pit_unavailable"


def test_exact_close_boundary_is_not_treated_as_closed():
    received = datetime(2026, 1, 1, tzinfo=UTC)
    exact_close = int(received.timestamp() * 1000)
    payload = [[1767225540000, "1", "1", "1", "1", "1", exact_close, "1", 1, "1", "1", "0"]]
    source = BinanceCoinMContinuousKlineDataSource("BTCUSD", "PERPETUAL", "1m", transport=FakeTransport(payload, received))
    snapshot = source.fetch_snapshot(as_of=received)
    assert snapshot.metadata.quality is DataQualityStatus.UNAVAILABLE
    assert snapshot.values["error_class"] == "pit_unavailable"


def test_contract_and_span_constraints_are_enforced():
    try:
        BinanceCoinMContinuousKlineDataSource("BTCUSD", "BAD", "1m")
    except ValueError:
        pass
    else:
        raise AssertionError("invalid contract type must be rejected")
    start = datetime(2025, 1, 1, tzinfo=UTC)
    end = datetime(2025, 8, 1, tzinfo=UTC)
    try:
        BinanceCoinMContinuousKlineDataSource("BTCUSD", "PERPETUAL", "1m", start_time=start, end_time=end)
    except ValueError:
        pass
    else:
        raise AssertionError("span > 200 days must be rejected")


def test_adapter_is_read_only():
    assert not hasattr(BinanceCoinMContinuousKlineDataSource, "place_order")
