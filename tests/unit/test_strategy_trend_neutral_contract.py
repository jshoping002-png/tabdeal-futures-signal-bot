from datetime import timedelta

from tabdeal_signal.data.contracts import MarketSnapshot
from tabdeal_signal.domain.contracts import Candle, DecisionContext, Direction
from tabdeal_signal.strategy.contracts import StrategyEvaluationRequest
from tabdeal_signal.strategy.engine import MultiTimeframeStrategyEvaluator
from tests.unit.test_strategy_determinism_contract import BASE, request


def test_strategy_evaluation_blocks_when_4h_trend_is_neutral():
    request_value = request()
    snapshot = request_value.snapshot
    candles = list(snapshot.candles)

    # Remove the higher high that establishes the LONG 4H trend while keeping
    # the series structurally valid and the lower-timeframe inputs unchanged.
    target_time = BASE + timedelta(hours=24)
    for index, candle in enumerate(candles):
        if candle.timeframe == "4h" and candle.open_time == target_time:
            candles[index] = Candle(
                candle.symbol,
                candle.timeframe,
                candle.open_time,
                candle.close_time,
                candle.open,
                10.0,
                candle.low,
                candle.close,
                candle.volume,
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
