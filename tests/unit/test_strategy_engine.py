from datetime import datetime, timedelta, timezone

import pytest

from tabdeal_signal.data.contracts import MarketSnapshot
from tabdeal_signal.domain.contracts import Candle, DecisionContext, Direction
from tabdeal_signal.strategy.contracts import StrategyEvaluationRequest
from tabdeal_signal.strategy.engine import (
    MultiTimeframeStrategyEvaluator,
    _break_events,
    _confirmed_swings,
    _latest_bos_and_choch,
    _trend,
)

UTC = timezone.utc


def make_candle(i, high=10.0, low=1.0, close=None):
    start = datetime(2026, 1, 1, tzinfo=UTC) + i * timedelta(minutes=15)
    if close is None:
        close = (high + low) / 2
    return Candle("BTCUSDT", "15m", start, start + timedelta(minutes=15), low, high, low, close, 1.0)


def test_strict_swing_high_is_confirmed_by_two_following_candles():
    candles = tuple(make_candle(i, high=20.0 if i == 2 else 10.0) for i in range(5))
    swings = _confirmed_swings(candles, high=True)
    assert len(swings) == 1
    assert swings[0].index == 2
    assert swings[0].price == 20.0
    assert swings[0].confirmed_at == candles[4].close_time


def test_equal_neighbor_is_not_a_swing():
    candles = tuple(make_candle(i, high=20.0 if i in (2, 3) else 10.0) for i in range(5))
    assert _confirmed_swings(candles, high=True) == ()


def test_strict_swing_low_is_confirmed():
    candles = tuple(make_candle(i, low=0.0 if i == 2 else 1.0) for i in range(5))
    swings = _confirmed_swings(candles, high=False)
    assert len(swings) == 1
    assert swings[0].index == 2
    assert swings[0].price == 0.0


def test_four_hour_higher_high_and_higher_low_confirm_long_trend():
    candles = tuple(
        make_candle(
            i,
            high={2: 20.0, 6: 25.0}.get(i, 10.0),
            low={4: 5.0, 8: 6.0}.get(i, 7.0),
        )
        for i in range(11)
    )
    reference_time = candles[-1].close_time + timedelta(minutes=1)
    assert _trend(candles, reference_time) is Direction.LONG


def test_four_hour_lower_high_and_lower_low_confirm_short_trend():
    candles = tuple(
        make_candle(
            i,
            high={2: 20.0, 6: 15.0}.get(i, 10.0),
            low={4: 6.0, 8: 5.0}.get(i, 7.0),
        )
        for i in range(11)
    )
    reference_time = candles[-1].close_time + timedelta(minutes=1)
    assert _trend(candles, reference_time) is Direction.SHORT


def test_four_hour_mixed_structure_is_unresolved():
    candles = tuple(
        make_candle(
            i,
            high={2: 20.0, 6: 25.0}.get(i, 10.0),
            low={4: 5.0, 8: 8.0}.get(i, 7.0),
        )
        for i in range(11)
    )
    reference_time = candles[-1].close_time + timedelta(minutes=1)
    assert _trend(candles, reference_time) is None


def test_break_event_requires_close_strictly_beyond_confirmed_swing_high():
    candles = tuple(
        make_candle(
            i,
            high=20.0 if i == 2 else (21.0 if i == 5 else 10.0),
            low=1.0,
            close=21.0 if i == 5 else 5.0,
        )
        for i in range(7)
    )
    reference_time = candles[-1].close_time + timedelta(minutes=1)
    events = _break_events(candles, reference_time)
    assert events == ((candles[5].close_time, Direction.LONG),)


def test_break_event_requires_close_strictly_below_confirmed_swing_low():
    candles = tuple(
        make_candle(
            i,
            high=10.0,
            low=0.5 if i == 2 else (0.3 if i == 5 else 1.0),
            close=0.4 if i == 5 else 7.0,
        )
        for i in range(7)
    )
    reference_time = candles[-1].close_time + timedelta(minutes=1)
    events = _break_events(candles, reference_time)
    assert events == ((candles[5].close_time, Direction.SHORT),)


def test_break_event_at_confirmation_boundary_is_not_lookahead_valid():
    candles = tuple(
        make_candle(
            i,
            high=20.0 if i == 2 else (21.0 if i == 4 else 10.0),
            low=1.0,
            close=21.0 if i == 4 else (20.0 if i == 2 else 5.0),
        )
        for i in range(7)
    )
    reference_time = candles[-1].close_time + timedelta(minutes=1)
    events = _break_events(candles, reference_time)
    assert events == ()


def test_latest_bos_and_choch_separates_trend_bos_from_later_opposite_choch():
    candles = tuple(
        make_candle(
            i,
            high=21.0 if i == 5 else (20.0 if i == 2 else 10.0),
            low=0.0 if i == 6 else (-1.0 if i == 9 else 1.0),
            close=21.0 if i == 5 else (-1.0 if i == 9 else 5.0),
        )
        for i in range(11)
    )
    reference_time = candles[-1].close_time + timedelta(minutes=1)

    latest_bos, latest_choch = _latest_bos_and_choch(candles, reference_time, Direction.LONG)

    assert latest_bos == (candles[5].close_time, Direction.LONG)
    assert latest_choch == (candles[9].close_time, Direction.SHORT)


def test_evaluator_rejects_empty_symbol():
    with pytest.raises(ValueError):
        MultiTimeframeStrategyEvaluator(symbol="", direction=Direction.LONG)


def test_evaluator_rejects_non_direction_value():
    with pytest.raises(ValueError):
        MultiTimeframeStrategyEvaluator(symbol="BTCUSDT", direction="LONG")


def test_evaluator_rejects_invalid_request_type():
    evaluator = MultiTimeframeStrategyEvaluator(symbol="BTCUSDT", direction=Direction.LONG)
    with pytest.raises(ValueError, match="request must be a StrategyEvaluationRequest"):
        evaluator.evaluate(object())


def test_evaluator_preserves_symbol_and_direction_configuration():
    evaluator = MultiTimeframeStrategyEvaluator(symbol=" BTCUSDT ", direction=Direction.SHORT)
    assert evaluator.symbol == " BTCUSDT "
    assert evaluator.direction is Direction.SHORT


def test_evaluator_blocks_when_any_required_timeframe_is_missing():
    opened_at = datetime(2026, 1, 1, tzinfo=UTC)
    candle = Candle("BTCUSDT", "15m", opened_at, opened_at + timedelta(minutes=15), 1, 2, 1, 1.5, 1)
    snapshot = MarketSnapshot(
        "snap-1",
        "source-a",
        candle.close_time + timedelta(microseconds=1),
        (candle,),
    )
    context = DecisionContext(
        decision_time=snapshot.reference_time,
        reference_time=snapshot.reference_time,
        snapshot_id="snap-1",
        config_version="config-1",
    )
    request = StrategyEvaluationRequest(context, snapshot)

    result = MultiTimeframeStrategyEvaluator(symbol="BTCUSDT", direction=Direction.LONG).evaluate(request)

    assert result.direction is Direction.LONG
    assert result.eligible is False
    assert result.reason_code == "INSUFFICIENT_SWING_CONTEXT"
