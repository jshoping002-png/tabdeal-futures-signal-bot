from datetime import datetime

from tabdeal_signal.domain.contracts import DecisionContext, DecisionStatus, Direction, SideDecision, UTC
from tabdeal_signal.risk.contracts import RiskEvaluation
from tabdeal_signal.risk.gate import apply_risk_gate


REFERENCE = datetime(2025, 1, 1, 12, tzinfo=UTC)


def context() -> DecisionContext:
    return DecisionContext(REFERENCE, REFERENCE, "snapshot-1", "config-1")


def signal(direction: Direction) -> SideDecision:
    return SideDecision(direction, DecisionStatus.SIGNAL, "STRATEGY_OK")


class AllowEvaluator:
    def __init__(self):
        self.calls = 0

    def evaluate(self, request):
        self.calls += 1
        return RiskEvaluation(request.decision.direction, True, "RISK_OK")


class BlockEvaluator:
    def evaluate(self, request):
        return RiskEvaluation(request.decision.direction, False, "RISK_BLOCKED")


def test_allowed_signal_passes_through_as_signal():
    evaluator = AllowEvaluator()
    result = apply_risk_gate(signal(Direction.LONG), context=context(), evaluator=evaluator)
    assert result.status is DecisionStatus.SIGNAL
    assert result.direction is Direction.LONG
    assert result.reason_code == "RISK_OK"
    assert evaluator.calls == 1


def test_risk_policy_can_block_signal():
    result = apply_risk_gate(signal(Direction.SHORT), context=context(), evaluator=BlockEvaluator())
    assert result.status is DecisionStatus.BLOCKED
    assert result.direction is Direction.SHORT
    assert result.reason_code == "RISK_BLOCKED"


def test_already_blocked_decision_does_not_call_risk_evaluator():
    evaluator = AllowEvaluator()
    blocked = SideDecision(Direction.LONG, DecisionStatus.BLOCKED, "STRATEGY_BLOCKED")
    result = apply_risk_gate(blocked, context=context(), evaluator=evaluator)
    assert result == blocked
    assert evaluator.calls == 0
