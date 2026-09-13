from datetime import datetime, timezone

import pytest

from tabdeal_signal.decision.final import FinalDecision
from tabdeal_signal.domain.contracts import DecisionContext, DecisionStatus
from tabdeal_signal.notification.contracts import (
    NotificationOutcome,
    NotificationRequest,
    NotificationResult,
)
from tabdeal_signal.notification.dispatcher import dispatch_outbox_message
from tabdeal_signal.persistence.outbox import OutboxMessage


class FakeSender:
    def __init__(self, result: NotificationResult) -> None:
        self.result = result
        self.requests = []

    def send(self, request: NotificationRequest) -> NotificationResult:
        self.requests.append(request)
        return self.result


class FakeOutbox:
    def __init__(self) -> None:
        self.marked = []

    def mark_delivered(self, event_id: str) -> None:
        self.marked.append(event_id)


def make_request() -> NotificationRequest:
    decision_time = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    context = DecisionContext(
        decision_time=decision_time,
        reference_time=decision_time,
        snapshot_id="snapshot-1",
        config_version="v1",
    )
    message = OutboxMessage(
        event_id="event-1",
        idempotency_key="idem-1",
        context=context,
        decision=FinalDecision(status=DecisionStatus.BLOCKED, reason_code="NO_SIGNAL"),
        created_at=decision_time,
    )
    return NotificationRequest(message=message)


def test_delivery_marks_outbox_delivered() -> None:
    request = make_request()
    sender = FakeSender(NotificationResult(NotificationOutcome.DELIVERED, "DELIVERED"))
    outbox = FakeOutbox()

    result = dispatch_outbox_message(request=request, sender=sender, outbox=outbox)

    assert result.marked_delivered is True
    assert outbox.marked == ["event-1"]
    assert sender.requests == [request]


def test_duplicate_delivery_is_terminal_and_marks_outbox() -> None:
    request = make_request()
    sender = FakeSender(NotificationResult(NotificationOutcome.DUPLICATE, "ALREADY_DELIVERED"))
    outbox = FakeOutbox()

    result = dispatch_outbox_message(request=request, sender=sender, outbox=outbox)

    assert result.marked_delivered is True
    assert outbox.marked == ["event-1"]


@pytest.mark.parametrize(
    "outcome",
    [NotificationOutcome.RETRYABLE, NotificationOutcome.BLOCKED],
)
def test_non_terminal_delivery_does_not_mark_outbox(outcome: NotificationOutcome) -> None:
    request = make_request()
    sender = FakeSender(NotificationResult(outcome, outcome.value))
    outbox = FakeOutbox()

    result = dispatch_outbox_message(request=request, sender=sender, outbox=outbox)

    assert result.marked_delivered is False
    assert outbox.marked == []


def test_invalid_request_is_rejected() -> None:
    sender = FakeSender(NotificationResult(NotificationOutcome.DELIVERED, "DELIVERED"))
    outbox = FakeOutbox()

    with pytest.raises(ValueError, match="NotificationRequest"):
        dispatch_outbox_message(request=object(), sender=sender, outbox=outbox)
