from datetime import datetime, timezone

from tabdeal_signal.data.contracts import MarketSnapshot
from tabdeal_signal.decision.pipeline import evaluate_signal_sides
from tabdeal_signal.domain.contracts import Candle, DecisionContext, DecisionStatus, Direction
from tabdeal_signal.risk.contracts import RiskEvaluation
from tabdeal_signal.strategy.contracts import StrategyEvaluation, StrategyEvaluationRequest
from tabdeal_signal.strategy.isolation import IsolatedSideEvaluators


UTC = timezone.utc


class StrategyStub:
    def __init__(self, direction: Direction, eligible: bool, reason: str) -> None:
        self.direction = direction
        self.eligible = eligible
        self.reason = reason
        self.calls = 0

    def evaluate(self, request: StrategyEvaluationRequest) -> StrategyEvaluation:
        self.calls += 1
        return StrategyEvaluation(self.direction, self.eligible, self.reason)


class RiskStub:
    def __init__(self, allowed: bool, reason: str) -> None:
        self.allowed = allowed
        self.reason = reason
        self.calls = 0

    def evaluate(self, request):
        self.calls += 1
        return RiskEvaluation(request.decision.direction, self.allowed, self.reason)


class ConflictStub:
    def __init__(self) -> None:
        self.calls = 0

    def resolve(self, long_decision, short_decision):
        self.calls += 1
        return long_decision, short_decision


def context_and_snapshot():
    reference = datetime(2026, 1, 1, 1, 0, 0, 1, tzinfo=UTC)
    snapshot = MarketSnapshot(
        snapshot_id="snap-1",
        source_id="test-source",
        reference_time=reference,
        candles=(
            Candle(
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
        decision_time=reference,
        reference_time=reference,
        snapshot_id=snapshot.snapshot_id,
        config_version="v1",
    )
    return context, snapshot


def test_pipeline_preserves_independent_side_results_when_no_conflict():
    context, snapshot = context_and_snapshot()
    long_strategy = StrategyStub(Direction.LONG, True, "LONG_OK")
    short_strategy = StrategyStub(Direction.SHORT, False, "SHORT_NOT_READY")
    long_risk = RiskStub(True, "LONG_RISK_OK")
    short_risk = RiskStub(True, "SHORT_RISK_OK")
    conflict = ConflictStub()

    long_result, short_result = evaluate_signal_sides(
        context=context,
        snapshot=snapshot,
        evaluators=IsolatedSideEvaluators(long_strategy, short_strategy),
        conflict_resolver=conflict,
        long_risk_evaluator=long_risk,
        short_risk_evaluator=short_risk,
    )

    assert long_result.status is DecisionStatus.SIGNAL
    assert long_result.direction is Direction.LONG
    assert long_result.reason_code == "LONG_RISK_OK"
    assert short_result.status is DecisionStatus.BLOCKED
    assert short_result.direction is Direction.SHORT
    assert short_result.reason_code == "SHORT_NOT_READY"
    assert conflict.calls == 0
    assert long_risk.calls == 1
    assert short_risk.calls == 0


def test_pipeline_blocks_both_sides_when_both_strategy_paths_signal():
    context, snapshot = context_and_snapshot()
    long_strategy = StrategyStub(Direction.LONG, True, "LONG_OK")
    short_strategy = StrategyStub(Direction.SHORT, True, "SHORT_OK")
    long_risk = RiskStub(True, "LONG_RISK_OK")
    short_risk = RiskStub(True, "SHORT_RISK_OK")
    conflict = __import__("tabdeal_signal.strategy.conflict", fromlist=["BlockOnConflictResolver"]).BlockOnConflictResolver()

    long_result, short_result = evaluate_signal_sides(
        context=context,
        snapshot=snapshot,
        evaluators=IsolatedSideEvaluators(long_strategy, short_strategy),
        conflict_resolver=conflict,
        long_risk_evaluator=long_risk,
        short_risk_evaluator=short_risk,
    )

    assert long_result.status is DecisionStatus.BLOCKED
    assert short_result.status is DecisionStatus.BLOCKED
    assert long_result.reason_code == "CONFLICT_BOTH_DIRECTIONS"
    assert short_result.reason_code == "CONFLICT_BOTH_DIRECTIONS"
    assert long_risk.calls == 0
    assert short_risk.calls == 0
