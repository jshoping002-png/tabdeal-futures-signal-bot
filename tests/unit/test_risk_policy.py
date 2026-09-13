from datetime import datetime, timezone

import pytest

from tabdeal_signal.domain.contracts import DecisionContext, DecisionStatus, Direction, SideDecision
from tabdeal_signal.risk.contracts import RiskEvaluationRequest
from tabdeal_signal.risk.policy import SignalSafetyRiskPolicyV1

UTC = timezone.utc
REFERENCE = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def request(status: DecisionStatus = DecisionStatus.SIGNAL) -> RiskEvaluationRequest:
    return RiskEvaluationRequest(
        context=DecisionContext(
            decision_time=REFERENCE,
            reference_time=REFERENCE,
            snapshot_id="snapshot-1",
            config_version="config-1",
        ),
        decision=SideDecision(
            direction=Direction.LONG,
            status=status,
            reason_code="ENTRY_BREAKOUT_LONG" if status is DecisionStatus.SIGNAL else "NO_SIGNAL",
        ),
    )


def test_policy_accepts_valid_strategy_signal() -> None:
    result = SignalSafetyRiskPolicyV1().evaluate(request())

    assert result.direction is Direction.LONG
    assert result.allowed is True
    assert result.reason_code == "RISK_POLICY_ACCEPTED"


def test_policy_preserves_upstream_block_as_rejection() -> None:
    result = SignalSafetyRiskPolicyV1().evaluate(request(DecisionStatus.BLOCKED))

    assert result.direction is Direction.LONG
    assert result.allowed is False
    assert result.reason_code == "RISK_POLICY_UPSTREAM_BLOCKED"


def test_policy_is_deterministic() -> None:
    policy = SignalSafetyRiskPolicyV1()

    assert policy.evaluate(request()) == policy.evaluate(request())


def test_policy_rejects_invalid_request_type() -> None:
    with pytest.raises(ValueError, match="request must be a RiskEvaluationRequest"):
        SignalSafetyRiskPolicyV1().evaluate(object())


def test_policy_version_is_explicit() -> None:
    assert SignalSafetyRiskPolicyV1.policy_version == "risk-policy-v1"
