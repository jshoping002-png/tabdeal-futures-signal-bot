from datetime import datetime, timedelta, timezone

from tabdeal_signal.data.contracts import MarketSnapshot
from tabdeal_signal.domain.contracts import Candle, DecisionContext, DecisionStatus, Direction
from tabdeal_signal.strategy.contracts import StrategyEvaluationRequest
from tabdeal_signal.strategy.engine import MultiTimeframeStrategyEvaluator

UTC = timezone.utc
BASE = datetime(2026, 1, 1, tzinfo=UTC)


def make_candle(timeframe, start, duration, *, high=10.0, low=1.0, close=None):
    if close is None:
        close = (high + low) / 2
    return Candle(
        "BTCUSDT",
        timeframe,
        start,
        start + duration,
        low,
        high,
        low,
        close,
        1.0,
    )


def make_series(timeframe, count, start):
    durations = {"15m": timedelta(minutes=15), "1h": timedelta(hours=1), "4h": timedelta(hours=4)}
    duration = durations[timeframe]
    return tuple(make_candle(timeframe, start + i * duration, duration) for i in range(count))


def make_request(candles, reference_time):
    snapshot = MarketSnapshot("snapshot-v1", "test-source", reference_time, tuple(sorted(candles, key=lambda c: (c.symbol, c.timeframe, c.open_time))))
    context = DecisionContext(reference_time, reference_time, snapshot.snapshot_id, "strategy-v1")
    return StrategyEvaluationRequest(context, snapshot)


def long_fixture():
    candles_4h = list(make_series("4h", 11, BASE))
    for i, high, low in ((2, 20.0, 5.0), (4, 10.0, 1.0), (6, 25.0, 10.0), (8, 10.0, 6.0)):
        candle = candles_4h[i]
        candles_4h[i] = make_candle("4h", candle.open_time, timedelta(hours=4), high=high, low=low)

    candles_1h = list(make_series("1h", 7, BASE + timedelta(hours=48)))
    candles_1h[2] = make_candle("1h", candles_1h[2].open_time, timedelta(hours=1), high=20.0, low=1.0)
    candles_1h[5] = make_candle("1h", candles_1h[5].open_time, timedelta(hours=1), high=21.0, low=1.0, close=21.0)

    candles_15m = list(make_series("15m", 7, BASE + timedelta(hours=56)))
    candles_15m[2] = make_candle("15m", candles_15m[2].open_time, timedelta(minutes=15), high=20.0, low=1.0)
    candles_15m[5] = make_candle("15m", candles_15m[5].open_time, timedelta(minutes=15), high=21.0, low=1.0, close=21.0)

    return candles_4h + candles_1h + candles_15m


def test_strategy_contract_accepts_4h_trend_1h_bos_then_15m_breakout():
    candles = long_fixture()
    reference_time = max(c.close_time for c in candles) + timedelta(minutes=1)
    request = make_request(candles, reference_time)

    result = MultiTimeframeStrategyEvaluator(symbol="BTCUSDT", direction=Direction.LONG).evaluate(request)

    assert result.to_side_decision().status is DecisionStatus.SIGNAL
    assert result.reason_code == "ENTRY_BREAKOUT_LONG"


def test_strategy_contract_blocks_15m_breakout_that_precedes_1h_bos():
    candles = long_fixture()
    candles = [
        make_candle(c.timeframe, c.open_time - timedelta(hours=60) if c.timeframe == "15m" else c.open_time, timedelta(minutes=15) if c.timeframe == "15m" else (timedelta(hours=1) if c.timeframe == "1h" else timedelta(hours=4)), high=c.high, low=c.low, close=c.close)
        if c.timeframe == "15m" else c
        for c in candles
    ]
    reference_time = max(c.close_time for c in candles) + timedelta(minutes=1)
    request = make_request(candles, reference_time)

    result = MultiTimeframeStrategyEvaluator(symbol="BTCUSDT", direction=Direction.LONG).evaluate(request)

    assert result.to_side_decision().status is DecisionStatus.BLOCKED
    assert result.reason_code == "ENTRY_NOT_CONFIRMED"
