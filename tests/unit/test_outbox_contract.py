from datetime import datetime, timezone

import pytest

from tabdeal_signal.decision.final import FinalDecision
from tabdeal_signal.domain.contracts import DecisionContext, DecisionStatus
from tabdeal_signal.persistence.outbox import OutboxMessage, OutboxStatus


UTC = timezone.utc


def context() -> DecisionContext:
    return DecisionContext(
        decision_time=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
        reference_time=datetime(2026, 1, 1, 11, 59, tzinfo=UTC),
        snapshot_id="snapshot-1",
        config_version="config-1",
    )


def decision() -> FinalDecision:
    return FinalDecision(DecisionStatus.BLOCKED, reason_code="NO_SIGNAL")


def message(**overrides: object) -> OutboxMessage:
    values: dict[str, object] = dict(
        event_id="event-1",
        idempotency_key="snapshot-1:decision-1",
        context=context(),
        decision=decision(),
        created_at=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
    )
    values.update(overrides)
    return OutboxMessage(**values)


def test_outbox_message_requires_event_id() -> None:
    with pytest.raises(ValueError, match="event_id is required"):
        message(event_id=" ")


def test_outbox_message_requires_idempotency_key() -> None:
    with pytest.raises(ValueError, match="idempotency_key is required"):
        message(idempotency_key=" ")


def test_outbox_message_requires_context_and_decision() -> None:
    with pytest.raises(ValueError, match="context must be a DecisionContext"):
        message(context=None)
    with pytest.raises(ValueError, match="decision must be a FinalDecision"):
        message(decision=None)


def test_outbox_message_is_pending_by_default() -> None:
    item = message()
    assert item.status is OutboxStatus.PENDING


def test_outbox_message_rejects_naive_created_at() -> None:
    with pytest.raises(ValueError, match="created_at must use the context timezone"):
        message(created_at=datetime(2026, 1, 1, 12, 0))


def test_outbox_message_accepts_delivered_status() -> None:
    item = message(status=OutboxStatus.DELIVERED)
    assert item.status is OutboxStatus.DELIVERED


def test_outbox_message_rejects_invalid_created_at_type() -> None:
    with pytest.raises(ValueError, match="created_at must be a datetime"):
        message(created_at="2026-01-01T12:00:00Z")


def test_outbox_message_rejects_invalid_status_type() -> None:
    with pytest.raises(ValueError, match="status must be an OutboxStatus"):
        message(status="PENDING")
