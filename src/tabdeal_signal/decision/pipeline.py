from __future__ import annotations

from datetime import datetime

from tabdeal_signal.data.contracts import MarketSnapshot
from tabdeal_signal.decision.final import FinalDecision, resolve_final_decision
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


def evaluate_final_decision(
    *,
    context: DecisionContext,
    snapshot: MarketSnapshot,
    evaluators: IsolatedSideEvaluators,
    conflict_resolver: ConflictResolver,
    long_risk_evaluator: RiskEvaluator,
    short_risk_evaluator: RiskEvaluator,
    signal_id: str,
    created_at: datetime,
) -> FinalDecision:
    """Run the signal-only gates and resolve their result into one final outcome.

    Signal identity and creation time are explicit inputs; this boundary does not
    invent an ID scheme or obtain wall-clock time. No persistence or notification
    side effects occur here.
    """
    long_decision, short_decision = evaluate_signal_sides(
        context=context,
        snapshot=snapshot,
        evaluators=evaluators,
        conflict_resolver=conflict_resolver,
        long_risk_evaluator=long_risk_evaluator,
        short_risk_evaluator=short_risk_evaluator,
    )
    return resolve_final_decision(
        long_decision=long_decision,
        short_decision=short_decision,
        signal_id=signal_id,
        created_at=created_at,
        snapshot_id=context.snapshot_id,
        config_version=context.config_version,
    )
