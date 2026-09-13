from __future__ import annotations

from tabdeal_signal.domain.contracts import DecisionContext, DecisionStatus, SideDecision
from tabdeal_signal.risk.contracts import RiskEvaluationRequest, RiskEvaluator


def apply_risk_gate(
    decision: SideDecision,
    *,
    context: DecisionContext,
    evaluator: RiskEvaluator,
) -> SideDecision:
    """Apply one deterministic risk policy without changing decision direction."""
    if not isinstance(decision, SideDecision):
        raise ValueError("decision must be a SideDecision")
    if not isinstance(context, DecisionContext):
        raise ValueError("context must be a DecisionContext")
    if decision.status is DecisionStatus.BLOCKED:
        return decision

    evaluation = evaluator.evaluate(RiskEvaluationRequest(context=context, decision=decision))
    return evaluation.to_side_decision(decision)
