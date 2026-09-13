from __future__ import annotations

from tabdeal_signal.data.contracts import MarketSnapshot
from tabdeal_signal.domain.contracts import DecisionContext, SideDecision
from tabdeal_signal.risk.contracts import RiskEvaluator
from tabdeal_signal.risk.gate import apply_risk_gate
from tabdeal_signal.strategy.contracts import StrategyEvaluationRequest
from tabdeal_signal.strategy.conflict import ConflictResolver, apply_conflict_gate
from tabdeal_signal.strategy.isolation import IsolatedSideEvaluators


def evaluate_signal_sides(
    *,
    context: DecisionContext,
    snapshot: MarketSnapshot,
    evaluators: IsolatedSideEvaluators,
    conflict_resolver: ConflictResolver,
    long_risk_evaluator: RiskEvaluator,
    short_risk_evaluator: RiskEvaluator,
) -> tuple[SideDecision, SideDecision]:
    """Evaluate both sides through strategy, conflict, and risk gates.

    This is deliberately a signal-only boundary: it creates no orders or positions
    and performs no persistence or notification side effects.
    """
    request = StrategyEvaluationRequest(context=context, snapshot=snapshot)
    long_decision = evaluators.evaluate_long(request).to_side_decision()
    short_decision = evaluators.evaluate_short(request).to_side_decision()

    long_decision, short_decision = apply_conflict_gate(
        long_decision,
        short_decision,
        resolver=conflict_resolver,
    )

    long_decision = apply_risk_gate(
        long_decision,
        context=context,
        evaluator=long_risk_evaluator,
    )
    short_decision = apply_risk_gate(
        short_decision,
        context=context,
        evaluator=short_risk_evaluator,
    )
    return long_decision, short_decision
