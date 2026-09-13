from datetime import datetime, timezone

import pytest

from tabdeal_signal.decision.final import FinalDecision
from tabdeal_signal.domain.contracts import DecisionContext, DecisionStatus
from tabdeal_signal.notification.contracts import (
    NotificationOutcome,
    NotificationRequest,
    NotificationResult,
)
from tabdeal_signal.persistence.outbox import OutboxMessage


def make_message() -> OutboxMessage:
    decision_time = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    context = DecisionContext(
        decision_time=decision_time,
        reference_time=decision_time,
        snapshot_id="snapshot-1",
        config_version="v1",
    )
    decision = FinalDecision(status=DecisionStatus.BLOCKED, reason_code="NO_SIGNAL")
    return OutboxMessage(
        event_id="event-1",
        idempotency_key="idem-1",
        context=context,
        decision=decision,
        created_at=decision_time,
    )


def test_notification_request_requires_outbox_message() -> None:
    with pytest.raises(ValueError, match="OutboxMessage"):
        NotificationRequest(message=object())


def test_notification_result_requires_explicit_outcome_and_reason() -> None:
    result = NotificationResult(NotificationOutcome.DELIVERED, "DELIVERED")
    assert result.retryable is False

    with pytest.raises(ValueError, match="reason_code"):
        NotificationResult(NotificationOutcome.RETRYABLE, "")


def test_retryable_result_is_explicit() -> None:
    result = NotificationResult(NotificationOutcome.RETRYABLE, "TEMPORARY_FAILURE")
    assert result.retryable is True


def test_all_delivery_outcomes_are_transport_neutral() -> None:
    message = make_message()
    request = NotificationRequest(message=message)
    assert request.message is message

    for outcome in NotificationOutcome:
        result = NotificationResult(outcome, outcome.value)
        assert result.outcome is outcome
