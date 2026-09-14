from datetime import datetime, timedelta, timezone

from tabdeal_signal.data.contracts import MarketSnapshot
from tabdeal_signal.domain.contracts import Candle, DecisionContext, DecisionStatus, Direction
from tabdeal_signal.strategy.contracts import StrategyEvaluationRequest
from tabdeal_signal.strategy.engine import MultiTimeframeStrategyEvaluator

UTC = timezone.utc
BASE = datetime(2026, 1, 1, tzinfo=UTC)


def candle(timeframe, start, duration, *, high=10.0, low=1.0, close=None):
    if close is None:
        close = (high + low) / 2
    return Candle("BTCUSDT", timeframe, start, start + duration, low, high, low, close, 1.0)


def request():
    candles_4h = [candle("4h", BASE + i * timedelta(hours=4), timedelta(hours=4), low=7.0) for i in range(11)]
    for i, high, low in ((2, 20.0, 7.0), (4, 10.0, 5.0), (6, 25.0, 7.0), (8, 10.0, 6.0)):
        candles_4h[i] = candle("4h", candles_4h[i].open_time, timedelta(hours=4), high=high, low=low)
    candles_1h = [candle("1h", BASE + timedelta(hours=48) + i * timedelta(hours=1), timedelta(hours=1)) for i in range(7)]
    candles_1h[2] = candle("1h", candles_1h[2].open_time, timedelta(hours=1), high=20.0, low=1.0)
    candles_1h[5] = candle("1h", candles_1h[5].open_time, timedelta(hours=1), high=21.0, low=1.0, close=21.0)
    candles_15m = [candle("15m", BASE + timedelta(hours=56) + i * timedelta(minutes=15), timedelta(minutes=15)) for i in range(7)]
    candles_15m[2] = candle("15m", candles_15m[2].open_time, timedelta(minutes=15), high=20.0, low=1.0)
    candles_15m[5] = candle("15m", candles_15m[5].open_time, timedelta(minutes=15), high=21.0, low=1.0, close=21.0)
    all_candles = tuple(candles_4h + candles_1h + candles_15m)
    reference_time = max(c.close_time for c in all_candles) + timedelta(minutes=1)
    snapshot = MarketSnapshot("snapshot-determinism", "test-source", reference_time, tuple(sorted(all_candles, key=lambda c: (c.symbol, c.timeframe, c.open_time))))
    context = DecisionContext(reference_time, reference_time, snapshot.snapshot_id, "strategy-v1")
    return StrategyEvaluationRequest(context, snapshot)


def test_strategy_evaluation_is_deterministic_for_identical_snapshot_and_reference():
    evaluator = MultiTimeframeStrategyEvaluator(symbol="BTCUSDT", direction=Direction.LONG)
    first = evaluator.evaluate(request())
    second = evaluator.evaluate(request())
    assert first == second
    assert first.to_side_decision().status is DecisionStatus.SIGNAL
    assert first.reason_code == "ENTRY_BREAKOUT_LONG"


def test_strategy_evaluation_rejects_snapshot_data_unavailable_at_reference_time():
    request_value = request()
    reference_time = request_value.context.reference_time
    future_candle = candle("15m", reference_time, timedelta(minutes=15), high=1000.0, low=1.0, close=1000.0)
    try:
        MarketSnapshot(request_value.snapshot.snapshot_id, request_value.snapshot.source_id, reference_time, tuple(sorted(request_value.snapshot.candles + (future_candle,), key=lambda c: (c.symbol, c.timeframe, c.open_time))))
    except ValueError as exc:
        assert str(exc) == "snapshot contains data unavailable at reference_time"
    else:
        raise AssertionError("future snapshot data must be rejected")


def test_long_and_short_evaluators_are_isolated():
    snapshot_request = request()
    long_result = MultiTimeframeStrategyEvaluator(symbol="BTCUSDT", direction=Direction.LONG).evaluate(snapshot_request)
    short_result = MultiTimeframeStrategyEvaluator(symbol="BTCUSDT", direction=Direction.SHORT).evaluate(snapshot_request)
    assert long_result.direction is Direction.LONG
    assert long_result.eligible is True
    assert long_result.reason_code == "ENTRY_BREAKOUT_LONG"
    assert short_result.direction is Direction.SHORT
    assert short_result.eligible is False
    assert short_result.reason_code == "TREND_LONG_CONFIRMED"


def test_strategy_evaluation_blocks_when_1h_bos_is_missing():
    request_value = request()
    snapshot = request_value.snapshot
    modified_candles = tuple(Candle(c.symbol, c.timeframe, c.open_time, c.close_time, c.open, c.high, c.low, 19.0 if c.timeframe == "1h" and c.open_time == BASE + timedelta(hours=53) else c.close, c.volume) for c in snapshot.candles)
    modified_snapshot = MarketSnapshot(snapshot.snapshot_id, snapshot.source_id, snapshot.reference_time, modified_candles)
    modified_request = StrategyEvaluationRequest(request_value.context, modified_snapshot)
    result = MultiTimeframeStrategyEvaluator(symbol="BTCUSDT", direction=Direction.LONG).evaluate(modified_request)
    assert result.eligible is False
    assert result.reason_code == "ENTRY_NOT_CONFIRMED"


def test_strategy_evaluation_blocks_when_15m_breakout_is_missing():
    request_value = request()
    snapshot = request_value.snapshot
    modified_candles = tuple(Candle(c.symbol, c.timeframe, c.open_time, c.close_time, c.open, c.high, c.low, 19.0 if c.timeframe == "15m" and c.open_time == BASE + timedelta(hours=57, minutes=15) else c.close, c.volume) for c in snapshot.candles)
    modified_snapshot = MarketSnapshot(snapshot.snapshot_id, snapshot.source_id, snapshot.reference_time, modified_candles)
    modified_request = StrategyEvaluationRequest(request_value.context, modified_snapshot)
    result = MultiTimeframeStrategyEvaluator(symbol="BTCUSDT", direction=Direction.LONG).evaluate(modified_request)
    assert result.eligible is False
    assert result.reason_code == "ENTRY_NOT_CONFIRMED"


def test_strategy_evaluation_blocks_after_confirmed_choch():
    request_value = request()
    snapshot = request_value.snapshot
    candles = list(snapshot.candles)
    swing_low_time = BASE + timedelta(hours=51)
    choch_time = BASE + timedelta(hours=54)
    for i, c in enumerate(candles):
        if c.timeframe == "1h" and c.open_time == swing_low_time:
            candles[i] = Candle(c.symbol, c.timeframe, c.open_time, c.close_time, c.open, c.high, 0.5, 5.0, c.volume)
        elif c.timeframe == "1h" and c.open_time == choch_time:
            candles[i] = Candle(c.symbol, c.timeframe, c.open_time, c.close_time, c.open, c.high, 0.1, 0.4, c.volume)
    modified_snapshot = MarketSnapshot(snapshot.snapshot_id, snapshot.source_id, snapshot.reference_time, tuple(candles))
    modified_request = StrategyEvaluationRequest(request_value.context, modified_snapshot)
    result = MultiTimeframeStrategyEvaluator(symbol="BTCUSDT", direction=Direction.LONG).evaluate(modified_request)
    assert result.eligible is False
    assert result.reason_code == "STRUCTURE_CHOCH_LONG_INVALIDATED"
