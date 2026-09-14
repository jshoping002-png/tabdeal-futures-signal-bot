from datetime import datetime, timedelta, timezone

from tabdeal_signal.data.contracts import MarketSnapshot
from tabdeal_signal.domain.contracts import Candle, DecisionContext, Direction
from tabdeal_signal.strategy.contracts import StrategyEvaluationRequest
from tabdeal_signal.strategy.engine import MultiTimeframeStrategyEvaluator

UTC = timezone.utc
BASE = datetime(2026, 1, 1, tzinfo=UTC)


def candle(timeframe, start, duration, *, high=10.0, low=1.0, close=None):
    if close is None:
        close = (high + low) / 2
    return Candle(
        "BTCUSDT", timeframe, start, start + duration, low, high, low, close, 1.0
    )


def build_request():
    candles_4h = [
        candle("4h", BASE + i * timedelta(hours=4), timedelta(hours=4), low=7.0)
        for i in range(11)
    ]
    for i, high, low in (
        (2, 20.0, 7.0),
        (4, 10.0, 5.0),
        (6, 25.0, 7.0),
        (8, 10.0, 6.0),
    ):
        candles_4h[i] = candle(
            "4h", candles_4h[i].open_time, timedelta(hours=4), high=high, low=low
        )

    candles_1h = [
        candle(
            "1h",
            BASE + timedelta(hours=48) + i * timedelta(hours=1),
            timedelta(hours=1),
        )
        for i in range(7)
    ]
    candles_1h[2] = candle(
        "1h", candles_1h[2].open_time, timedelta(hours=1), high=20.0, low=1.0
    )
    candles_1h[5] = candle(
        "1h",
        candles_1h[5].open_time,
        timedelta(hours=1),
        high=21.0,
        low=1.0,
        close=21.0,
    )

    candles_15m = [
        candle(
            "15m",
            BASE + timedelta(hours=56) + i * timedelta(minutes=15),
            timedelta(minutes=15),
        )
        for i in range(7)
    ]
    candles_15m[2] = candle(
        "15m", candles_15m[2].open_time, timedelta(minutes=15), high=20.0, low=1.0
    )
    candles_15m[5] = candle(
        "15m",
        candles_15m[5].open_time,
        timedelta(minutes=15),
        high=21.0,
        low=1.0,
        close=21.0,
    )

    all_candles = tuple(
        sorted(candles_4h + candles_1h + candles_15m, key=lambda c: (c.symbol, c.timeframe, c.open_time))
    )
    reference_time = max(c.close_time for c in all_candles) + timedelta(minutes=1)
    snapshot = MarketSnapshot(
        "snapshot-trend-neutral", "test-source", reference_time, all_candles
    )
    context = DecisionContext(
        reference_time, reference_time, snapshot.snapshot_id, "strategy-v1"
    )
    return StrategyEvaluationRequest(context, snapshot)


def test_strategy_evaluation_blocks_when_4h_trend_is_neutral():
    request_value = build_request()
    snapshot = request_value.snapshot
    candles = list(snapshot.candles)

    target_time = BASE + timedelta(hours=24)
    for index, candle_value in enumerate(candles):
        if candle_value.timeframe == "4h" and candle_value.open_time == target_time:
            candles[index] = Candle(
                candle_value.symbol,
                candle_value.timeframe,
                candle_value.open_time,
                candle_value.close_time,
                candle_value.open,
                16.0,
                candle_value.low,
                candle_value.close,
                candle_value.volume,
            )
            break

    modified_snapshot = MarketSnapshot(
        snapshot.snapshot_id,
        snapshot.source_id,
        snapshot.reference_time,
        tuple(candles),
    )
    modified_request = StrategyEvaluationRequest(request_value.context, modified_snapshot)
    result = MultiTimeframeStrategyEvaluator(
        symbol="BTCUSDT", direction=Direction.LONG
    ).evaluate(modified_request)

    assert result.eligible is False
    assert result.reason_code == "TREND_NEUTRAL"
