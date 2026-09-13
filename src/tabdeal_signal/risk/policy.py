from __future__ import annotations

from tabdeal_signal.domain.contracts import DecisionStatus, Direction
from tabdeal_signal.risk.contracts import RiskEvaluation, RiskEvaluationRequest, RiskEvaluator


class SignalSafetyRiskPolicyV1(RiskEvaluator):
    """Risk Policy V1: delivery safety only, with no financial risk model."""

    policy_version = "risk-policy-v1"

    def evaluate(self, request: RiskEvaluationRequest) -> RiskEvaluation:
        if not isinstance(request, RiskEvaluationRequest):
            raise ValueError("request must be a RiskEvaluationRequest")

        decision = request.decision
        context = request.context

        if decision.status is DecisionStatus.BLOCKED:
            return RiskEvaluation(
                direction=decision.direction,
                allowed=False,
                reason_code="RISK_POLICY_UPSTREAM_BLOCKED",
            )

        if decision.status is not DecisionStatus.SIGNAL:
            return RiskEvaluation(
                direction=decision.direction,
                allowed=False,
                reason_code="RISK_POLICY_INVALID_DECISION",
            )

        if context.reference_time > context.decision_time:
            return RiskEvaluation(
                direction=decision.direction,
                allowed=False,
                reason_code="RISK_POLICY_INVALID_CONTEXT",
            )

        if not context.config_version.strip() or not context.snapshot_id.strip():
            return RiskEvaluation(
                direction=decision.direction,
                allowed=False,
                reason_code="RISK_POLICY_INVALID_CONTEXT",
            )

        return RiskEvaluation(
            direction=decision.direction,
            allowed=True,
            reason_code="RISK_POLICY_ACCEPTED",
        )


__all__ = ["SignalSafetyRiskPolicyV1"]
