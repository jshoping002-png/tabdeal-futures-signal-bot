from datetime import datetime, timedelta, timezone

from tabdeal_signal.data.contracts import MarketSnapshot
from tabdeal_signal.domain.contracts import Candle, DecisionContext, DecisionStatus, Direction
from tabdeal_signal.strategy.contracts import StrategyEvaluationRequest
from tabdeal_signal.strategy.engine import MultiTimeframeStrategyEvaluator

UTC = timezone.utc
BASE = datetime(2026, 1, 1, tzinfo=UTC)


def make_candle(timeframe, start, duration, *, high=20.0, low=10.0, close=None):
    if close is None:
        close = (high + low) / 2
    return Candle("BTCUSDT", timeframe, start, start + duration, low, high, low, close, 1.0)


def short_request():
    candles_4h = [make_candle("4h", BASE + i * timedelta(hours=4), timedelta(hours=4), high=20.0, low=10.0) for i in range(11)]
    for i, high, low in ((2, 20.0, 10.0), (4, 25.0, 12.0), (6, 15.0, 11.0), (8, 14.0, 8.0)):
        candles_4h[i] = make_candle("4h", candles_4h[i].open_time, timedelta(hours=4), high=high, low=low)

    candles_1h = [make_candle("1h", BASE + timedelta(hours=48) + i * timedelta(hours=1), timedelta(hours=1)) for i in range(7)]
    candles_1h[2] = make_candle("1h", candles_1h[2].open_time, timedelta(hours=1), high=20.0, low=10.0)
    candles_1h[5] = make_candle("1h", candles_1h[5].open_time, timedelta(hours=1), high=19.0, low=9.0, close=9.0)

    candles_15m = [make_candle("15m", BASE + timedelta(hours=56) + i * timedelta(minutes=15), timedelta(minutes=15)) for i in range(7)]
    candles_15m[2] = make_candle("15m", candles_15m[2].open_time, timedelta(minutes=15), high=20.0, low=10.0)
    candles_15m[5] = make_candle("15m", candles_15m[5].open_time, timedelta(minutes=15), high=19.0, low=9.0, close=9.0)

    all_candles = tuple(candles_4h + candles_1h + candles_15m)
    reference_time = max(c.close_time for c in all_candles) + timedelta(minutes=1)
    snapshot = MarketSnapshot("snapshot-short-parity", "test-source", reference_time, tuple(sorted(all_candles, key=lambda c: (c.symbol, c.timeframe, c.open_time))))
    context = DecisionContext(reference_time, reference_time, snapshot.snapshot_id, "strategy-v1")
    return StrategyEvaluationRequest(context, snapshot)


def test_short_path_matches_contract_without_using_long_candidate_state():
    result = MultiTimeframeStrategyEvaluator(symbol="BTCUSDT", direction=Direction.SHORT).evaluate(short_request())

    assert result.to_side_decision().status is DecisionStatus.SIGNAL
    assert result.reason_code == "ENTRY_BREAKOUT_SHORT"
    assert result.direction is Direction.SHORT
