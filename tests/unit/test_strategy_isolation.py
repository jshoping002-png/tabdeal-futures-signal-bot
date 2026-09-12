from datetime import datetime, timezone

import pytest

from tabdeal_signal.data.contracts import MarketSnapshot
from tabdeal_signal.domain.contracts import DecisionContext, Direction
from tabdeal_signal.strategy.contracts import StrategyEvaluation, StrategyEvaluationRequest
from tabdeal_signal.strategy.isolation import IsolatedSideEvaluators


UTC = timezone.utc


class StubEvaluator:
    def __init__(self, direction: Direction, eligible: bool, reason: str) -> None:
        self.direction = direction
        self.eligible = eligible
        self.reason = reason
        self.calls = 0

    def evaluate(self, request: StrategyEvaluationRequest) -> StrategyEvaluation:
        self.calls += 1
        return StrategyEvaluation(self.direction, self.eligible, self.reason)


class WrongResultEvaluator(StubEvaluator):
    def __init__(self, declared: Direction, returned: Direction) -> None:
        super().__init__(declared, True, "WRONG_SIDE")
        self.returned = returned

    def evaluate(self, request: StrategyEvaluationRequest) -> StrategyEvaluation:
        self.calls += 1
        return StrategyEvaluation(self.returned, True, "WRONG_SIDE")


def request() -> StrategyEvaluationRequest:
    snapshot = MarketSnapshot(
        snapshot_id="snap-1",
        source_id="test-source",
        reference_time=datetime(2026, 1, 1, 1, tzinfo=UTC),
        candles=(
            __import__("tabdeal_signal.domain.contracts", fromlist=["Candle"]).Candle(
                symbol="BTCUSDT",
                timeframe="1h",
                open_time=datetime(2026, 1, 1, tzinfo=UTC),
                close_time=datetime(2026, 1, 1, 1, tzinfo=UTC),
                open=100.0,
                high=110.0,
                low=90.0,
                close=105.0,
                volume=1.0,
            ),
        ),
    )
    context = DecisionContext(
        decision_time=datetime(2026, 1, 1, 1, tzinfo=UTC),
        reference_time=snapshot.reference_time,
        snapshot_id=snapshot.snapshot_id,
        config_version="v1",
    )
    return StrategyEvaluationRequest(context=context, snapshot=snapshot)


def test_constructor_rejects_cross_wired_evaluators():
    long = StubEvaluator(Direction.LONG, True, "LONG_OK")
    short = StubEvaluator(Direction.SHORT, True, "SHORT_OK")
    with pytest.raises(ValueError, match="long_evaluator"):
        IsolatedSideEvaluators(long_evaluator=short, short_evaluator=short)
    with pytest.raises(ValueError, match="short_evaluator"):
        IsolatedSideEvaluators(long_evaluator=long, short_evaluator=long)


def test_long_and_short_are_evaluated_independently():
    long = StubEvaluator(Direction.LONG, True, "LONG_OK")
    short = StubEvaluator(Direction.SHORT, False, "SHORT_BLOCKED")
    isolated = IsolatedSideEvaluators(long_evaluator=long, short_evaluator=short)

    long_result = isolated.evaluate_long(request())
    short_result = isolated.evaluate_short(request())

    assert long_result.direction is Direction.LONG
    assert long_result.eligible is True
    assert short_result.direction is Direction.SHORT
    assert short_result.eligible is False
    assert long.calls == 1
    assert short.calls == 1


def test_evaluating_one_side_does_not_call_or_change_other_side():
    long = StubEvaluator(Direction.LONG, True, "LONG_OK")
    short = StubEvaluator(Direction.SHORT, True, "SHORT_OK")
    isolated = IsolatedSideEvaluators(long_evaluator=long, short_evaluator=short)

    isolated.evaluate_long(request())

    assert long.calls == 1
    assert short.calls == 0

    isolated.evaluate_short(request())
    assert long.calls == 1
    assert short.calls == 1


def test_long_side_rejects_wrong_direction_from_evaluator():
    isolated = IsolatedSideEvaluators(
        long_evaluator=WrongResultEvaluator(Direction.LONG, Direction.SHORT),
        short_evaluator=StubEvaluator(Direction.SHORT, True, "SHORT_OK"),
    )

    with pytest.raises(ValueError, match="non-LONG"):
        isolated.evaluate_long(request())


def test_short_side_rejects_wrong_direction_from_evaluator():
    isolated = IsolatedSideEvaluators(
        long_evaluator=StubEvaluator(Direction.LONG, True, "LONG_OK"),
        short_evaluator=WrongResultEvaluator(Direction.SHORT, Direction.LONG),
    )

    with pytest.raises(ValueError, match="non-SHORT"):
        isolated.evaluate_short(request())
