from datetime import datetime, timedelta, timezone

import pytest

from tabdeal_signal.data.contracts import MarketSnapshot
from tabdeal_signal.domain.contracts import Candle, DecisionContext, DecisionStatus, Direction
from tabdeal_signal.strategy.contracts import StrategyEvaluation, StrategyEvaluationRequest

UTC = timezone.utc


def candle(hour: int) -> Candle:
    start = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(hours=hour)
    return Candle("BTCUSDT", "1h", start, start + timedelta(hours=1), 100, 110, 90, 105, 1)


def context(reference_time: datetime) -> DecisionContext:
    return DecisionContext(
        decision_time=reference_time,
        reference_time=reference_time,
        snapshot_id="snap-1",
        config_version="config-1",
    )


def test_strategy_request_requires_matching_reference_time() -> None:
    snapshot = MarketSnapshot("snap-1", "source-a", candle(1).close_time + timedelta(microseconds=1), (candle(0), candle(1)))
    mismatched = context(snapshot.reference_time + timedelta(seconds=1))
    with pytest.raises(ValueError, match="reference_time"):
        StrategyEvaluationRequest(mismatched, snapshot)


def test_strategy_request_requires_matching_snapshot_id() -> None:
    snapshot = MarketSnapshot("snap-2", "source-a", candle(0).close_time + timedelta(microseconds=1), (candle(0),))
    with pytest.raises(ValueError, match="snapshot_id"):
        StrategyEvaluationRequest(context(snapshot.reference_time), snapshot)


def test_strategy_request_rejects_non_decision_context() -> None:
    snapshot = MarketSnapshot("snap-1", "source-a", candle(0).close_time + timedelta(microseconds=1), (candle(0),))
    with pytest.raises(ValueError, match="DecisionContext"):
        StrategyEvaluationRequest(object(), snapshot)  # type: ignore[arg-type]


def test_strategy_request_rejects_non_market_snapshot() -> None:
    reference_time = datetime(2026, 1, 1, 1, 0, 0, 1, tzinfo=UTC)
    with pytest.raises(ValueError, match="MarketSnapshot"):
        StrategyEvaluationRequest(context(reference_time), object())  # type: ignore[arg-type]


def test_strategy_evaluation_is_immutable_and_maps_to_side_decision() -> None:
    result = StrategyEvaluation(Direction.LONG, True, "LONG_RULES_PASS")
    assert result.to_side_decision().status is DecisionStatus.SIGNAL
    with pytest.raises(AttributeError):
        result.eligible = False  # type: ignore[misc]


def test_strategy_evaluation_maps_reason_code_without_mutation() -> None:
    result = StrategyEvaluation(Direction.LONG, True, "LONG_RULES_PASS")
    decision = result.to_side_decision()
    assert decision.reason_code == "LONG_RULES_PASS"
    assert decision.direction is Direction.LONG


def test_blocked_strategy_maps_to_blocked_side_decision() -> None:
    result = StrategyEvaluation(Direction.SHORT, False, "SHORT_DATA_INSUFFICIENT")
    decision = result.to_side_decision()
    assert decision.direction is Direction.SHORT
    assert decision.status is DecisionStatus.BLOCKED


def test_strategy_evaluation_requires_reason_code() -> None:
    with pytest.raises(ValueError, match="reason_code"):
        StrategyEvaluation(Direction.LONG, False, "")


def test_strategy_evaluation_rejects_whitespace_only_reason_code() -> None:
    with pytest.raises(ValueError, match="reason_code"):
        StrategyEvaluation(Direction.SHORT, True, "   \t\n")


def test_strategy_evaluation_requires_reason_code_string() -> None:
    with pytest.raises(ValueError, match="string"):
        StrategyEvaluation(Direction.LONG, False, 123)  # type: ignore[arg-type]


def test_strategy_evaluation_requires_direction_enum() -> None:
    with pytest.raises(ValueError, match="Direction"):
        StrategyEvaluation("LONG", True, "LONG_RULES_PASS")  # type: ignore[arg-type]


def test_strategy_evaluation_requires_boolean_eligibility() -> None:
    with pytest.raises(ValueError, match="bool"):
        StrategyEvaluation(Direction.LONG, 1, "LONG_RULES_PASS")  # type: ignore[arg-type]


def test_strategy_request_is_immutable() -> None:
    snapshot = MarketSnapshot("snap-1", "source-a", candle(1).close_time + timedelta(microseconds=1), (candle(0), candle(1)))
    request = StrategyEvaluationRequest(context(snapshot.reference_time), snapshot)
    with pytest.raises(AttributeError):
        request.context = request.context  # type: ignore[misc]
    with pytest.raises(AttributeError):
        request.snapshot = snapshot  # type: ignore[misc]


def test_strategy_request_rejects_non_string_context_snapshot_id() -> None:
    snapshot = MarketSnapshot("snap-1", "source-a", candle(0).close_time + timedelta(microseconds=1), (candle(0),))
    with pytest.raises(ValueError, match="snapshot_id and config_version must be strings"):
        invalid_context = DecisionContext(
            decision_time=snapshot.reference_time,
            reference_time=snapshot.reference_time,
            snapshot_id=123,  # type: ignore[arg-type]
            config_version="config-1",
        )
        StrategyEvaluationRequest(invalid_context, snapshot)


def test_strategy_request_rejects_non_string_context_config_version() -> None:
    snapshot = MarketSnapshot("snap-1", "source-a", candle(0).close_time + timedelta(microseconds=1), (candle(0),))
    with pytest.raises(ValueError, match="snapshot_id and config_version must be strings"):
        invalid_context = DecisionContext(
            decision_time=snapshot.reference_time,
            reference_time=snapshot.reference_time,
            snapshot_id="snap-1",
            config_version=123,  # type: ignore[arg-type]
        )
        StrategyEvaluationRequest(invalid_context, snapshot)
