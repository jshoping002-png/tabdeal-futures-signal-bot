from datetime import datetime, timedelta, timezone

from tabdeal_signal.data.contracts import MarketSnapshot
from tabdeal_signal.domain.contracts import Candle, DecisionContext, DecisionStatus, Direction
from tabdeal_signal.strategy.contracts import StrategyEvaluationRequest
from tabdeal_signal.strategy.engine import MultiTimeframeStrategyEvaluator

UTC = timezone.utc
BASE = datetime(2026, 1, 1, tzinfo=UTC)


def candle(
    timeframe,
    start,
    duration,
    *,
    high=10.0,
    low=1.0,
    close=None,
):
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


def request():
    candles_4h = [
        candle(
            "4h",
            BASE + i * timedelta(hours=4),
            timedelta(hours=4),
            low=7.0,
        )
        for i in range(11)
    ]

    for i, high, low in (
        (2, 20.0, 7.0),
        (4, 10.0, 5.0),
        (6, 25.0, 7.0),
        (8, 10.0, 6.0),
    ):
        candles_4h[i] = candle(
            "4h",
            candles_4h[i].open_time,
            timedelta(hours=4),
            high=high,
            low=low,
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
        "1h",
        candles_1h[2].open_time,
        timedelta(hours=1),
        high=20.0,
        low=1.0,
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
        "15m",
        candles_15m[2].open_time,
        timedelta(minutes=15),
        high=20.0,
        low=1.0,
    )

    candles_15m[5] = candle(
        "15m",
        candles_15m[5].open_time,
        timedelta(minutes=15),
        high=21.0,
        low=1.0,
        close=21.0,
    )

    all_candles = tuple(candles_4h + candles_1h + candles_15m)

    reference_time = max(
        c.close_time for c in all_candles
    ) + timedelta(minutes=1)

    snapshot = MarketSnapshot(
        "snapshot-determinism",
        "test-source",
        reference_time,
        tuple(
            sorted(
                all_candles,
                key=lambda c: (
                    c.symbol,
                    c.timeframe,
                    c.open_time,
                ),
            )
        ),
    )

    context = DecisionContext(
        reference_time,
        reference_time,
        snapshot.snapshot_id,
        "strategy-v1",
    )

    return StrategyEvaluationRequest(
        context,
        snapshot,
    )


def test_strategy_evaluation_is_deterministic_for_identical_snapshot_and_reference():
    evaluator = MultiTimeframeStrategyEvaluator(
        symbol="BTCUSDT",
        direction=Direction.LONG,
    )

    first = evaluator.evaluate(request())
    second = evaluator.evaluate(request())

    assert first == second
    assert first.to_side_decision().status is DecisionStatus.SIGNAL
    assert first.reason_code == "ENTRY_BREAKOUT_LONG"


def test_strategy_evaluation_does_not_use_post_reference_candles():
    request_value = request()
    reference_time = request_value.context.reference_time

    future_candle = candle(
        "15m",
        reference_time,
        timedelta(minutes=15),
        high=1000.0,
        low=1.0,
        close=1000.0,
    )

    snapshot = MarketSnapshot(
        request_value.snapshot.snapshot_id,
        request_value.snapshot.source_id,
        reference_time,
        request_value.snapshot.candles + (future_candle,),
    )

    context = DecisionContext(
        reference_time,
        reference_time,
        snapshot.snapshot_id,
        "strategy-v1",
    )

    future_request = StrategyEvaluationRequest(
        context,
        snapshot,
    )

    evaluator = MultiTimeframeStrategyEvaluator(
        symbol="BTCUSDT",
        direction=Direction.LONG,
    )

    assert evaluator.evaluate(future_request) == evaluator.evaluate(request_value)
