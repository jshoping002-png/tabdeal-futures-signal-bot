from datetime import timedelta

from tabdeal_signal.domain.contracts import Direction
from tabdeal_signal.strategy.engine import MultiTimeframeStrategyEvaluator, _break_events
from tests.unit.test_strategy_determinism_contract import request


def test_15m_breakout_requires_strict_close_beyond_level():
    snapshot_request = request()
    candles_15m = snapshot_request.snapshot.candles_for("BTCUSDT", "15m")
    reference_time = snapshot_request.context.reference_time

    # The existing fixture contains a confirmed LONG 1H BOS at 21.0.
    # Make the 15m candidate close exactly equal to that level: equality is not a breakout.
    from tabdeal_signal.domain.contracts import Candle

    modified = list(snapshot_request.snapshot.candles)
    target_time = candles_15m[5].open_time
    for index, candle in enumerate(modified):
        if candle.timeframe == "15m" and candle.open_time == target_time:
            modified[index] = Candle(
                candle.symbol,
                candle.timeframe,
                candle.open_time,
                candle.close_time,
                candle.open,
                candle.high,
                candle.low,
                21.0,
                candle.volume,
            )

    from tabdeal_signal.data.contracts import MarketSnapshot
    from tabdeal_signal.strategy.contracts import StrategyEvaluationRequest

    snapshot = MarketSnapshot(
        snapshot_request.snapshot.snapshot_id,
        snapshot_request.snapshot.source_id,
        reference_time,
        tuple(modified),
    )
    modified_request = StrategyEvaluationRequest(snapshot_request.context, snapshot)
    result = MultiTimeframeStrategyEvaluator(
        symbol="BTCUSDT", direction=Direction.LONG
    ).evaluate(modified_request)

    assert result.eligible is False
    assert result.reason_code == "ENTRY_NOT_CONFIRMED"
