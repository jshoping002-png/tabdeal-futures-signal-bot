from datetime import datetime, timezone

import pytest

from tabdeal_signal.decision.final import FinalDecision
from tabdeal_signal.domain.contracts import DecisionContext, DecisionStatus
from tabdeal_signal.persistence.contracts import PersistenceRequest, PersistenceResult


UTC = timezone.utc


def context() -> DecisionContext:
    return DecisionContext(
        decision_time=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
        reference_time=datetime(2026, 1, 1, 11, 59, tzinfo=UTC),
        snapshot_id="snapshot-1",
        config_version="config-1",
    )


def blocked_decision() -> FinalDecision:
    return FinalDecision(DecisionStatus.BLOCKED, reason_code="NO_SIGNAL")


def test_persistence_request_requires_explicit_idempotency_key() -> None:
    with pytest.raises(ValueError, match="idempotency_key is required"):
        PersistenceRequest(context=context(), decision=blocked_decision(), idempotency_key=" ")


def test_persistence_request_keeps_context_and_decision_together() -> None:
    request = PersistenceRequest(
        context=context(),
        decision=blocked_decision(),
        idempotency_key="snapshot-1:decision-1",
    )

    assert request.context.snapshot_id == "snapshot-1"
    assert request.decision.status is DecisionStatus.BLOCKED
    assert request.idempotency_key == "snapshot-1:decision-1"


def test_persistence_result_rejects_non_persisted_replay() -> None:
    with pytest.raises(ValueError, match="idempotent replay must be persisted"):
        PersistenceResult(persisted=False, idempotent_replay=True)


def test_persistence_result_accepts_new_persistence() -> None:
    result = PersistenceResult(persisted=True)

    assert result.persisted is True
    assert result.idempotent_replay is False


def test_persistence_result_accepts_idempotent_replay() -> None:
    result = PersistenceResult(persisted=True, idempotent_replay=True)

    assert result.persisted is True
    assert result.idempotent_replay is True
