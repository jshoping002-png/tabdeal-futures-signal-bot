from datetime import datetime, timedelta, timezone

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
from tabdeal_signal.persistence.reliability import OutboxLease


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

    def mark_delivered(self, event_id: str, lease: OutboxLease) -> None:
        self.marked.append((event_id, lease))


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


def make_lease(*, event_id: str = "event-1", expires_in: int = 60) -> OutboxLease:
    acquired_at = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    return OutboxLease(
        event_id=event_id,
        lease_token="lease-1",
        owner_id="worker-1",
        acquired_at=acquired_at,
        expires_at=acquired_at + timedelta(seconds=expires_in),
    )


def dispatch(request, sender, outbox, lease=None, reference_time=None):
    if lease is None:
        lease = make_lease()
    if reference_time is None:
        reference_time = lease.acquired_at
    return dispatch_outbox_message(
        request=request,
        sender=sender,
        outbox=outbox,
        lease=lease,
        reference_time=reference_time,
    )


def test_delivery_marks_outbox_delivered_under_exact_lease() -> None:
    request = make_request()
    sender = FakeSender(NotificationResult(NotificationOutcome.DELIVERED, "DELIVERED"))
    outbox = FakeOutbox()
    lease = make_lease()

    result = dispatch(request, sender, outbox, lease=lease)

    assert result.marked_delivered is True
    assert outbox.marked == [("event-1", lease)]
    assert sender.requests == [request]


def test_duplicate_delivery_is_terminal_and_marks_outbox() -> None:
    request = make_request()
    sender = FakeSender(NotificationResult(NotificationOutcome.DUPLICATE, "ALREADY_DELIVERED"))
    outbox = FakeOutbox()
    lease = make_lease()

    result = dispatch(request, sender, outbox, lease=lease)

    assert result.marked_delivered is True
    assert outbox.marked == [("event-1", lease)]


@pytest.mark.parametrize(
    "outcome",
    [NotificationOutcome.RETRYABLE, NotificationOutcome.BLOCKED],
)
def test_non_terminal_delivery_does_not_mark_outbox(outcome: NotificationOutcome) -> None:
    request = make_request()
    sender = FakeSender(NotificationResult(outcome, outcome.value))
    outbox = FakeOutbox()
    lease = make_lease()

    result = dispatch(request, sender, outbox, lease=lease)

    assert result.marked_delivered is False
    assert outbox.marked == []


def test_expired_lease_is_rejected_before_sender_call() -> None:
    request = make_request()
    sender = FakeSender(NotificationResult(NotificationOutcome.DELIVERED, "DELIVERED"))
    outbox = FakeOutbox()
    lease = make_lease(expires_in=60)
    reference_time = lease.expires_at

    with pytest.raises(ValueError, match="expired"):
        dispatch(request, sender, outbox, lease=lease, reference_time=reference_time)

    assert sender.requests == []
    assert outbox.marked == []


def test_lease_for_different_event_is_rejected_before_sender_call() -> None:
    request = make_request()
    sender = FakeSender(NotificationResult(NotificationOutcome.DELIVERED, "DELIVERED"))
    outbox = FakeOutbox()
    lease = make_lease(event_id="other-event")

    with pytest.raises(ValueError, match="event_id"):
        dispatch(request, sender, outbox, lease=lease)

    assert sender.requests == []
    assert outbox.marked == []


def test_invalid_request_is_rejected() -> None:
    sender = FakeSender(NotificationResult(NotificationOutcome.DELIVERED, "DELIVERED"))
    outbox = FakeOutbox()

    with pytest.raises(ValueError, match="NotificationRequest"):
        dispatch(object(), sender, outbox)


def test_delivery_rejects_reference_before_lease_acquisition() -> None:
    request = make_request()
    sender = FakeSender(NotificationResult(NotificationOutcome.DELIVERED, "DELIVERED"))
    outbox = FakeOutbox()
    lease = make_lease()
    with pytest.raises(ValueError, match="precede lease acquisition"):
        dispatch(request, sender, outbox, lease=lease, reference_time=lease.acquired_at - timedelta(seconds=1))
    assert sender.requests == []
    assert outbox.marked == []


def test_delivery_rejects_already_delivered_message() -> None:
    from tabdeal_signal.persistence.outbox import OutboxStatus

    request = make_request()
    delivered = OutboxMessage(
        event_id=request.message.event_id,
        idempotency_key=request.message.idempotency_key,
        context=request.message.context,
        decision=request.message.decision,
        created_at=request.message.created_at,
        status=OutboxStatus.DELIVERED,
    )
    request = NotificationRequest(message=delivered)
    sender = FakeSender(NotificationResult(NotificationOutcome.DELIVERED, "DELIVERED"))
    outbox = FakeOutbox()
    with pytest.raises(ValueError, match="must be PENDING"):
        dispatch(request, sender, outbox)
    assert sender.requests == []


def test_delivery_rejects_sender_without_send_method() -> None:
    request = make_request()
    outbox = FakeOutbox()
    with pytest.raises(ValueError, match="callable send"):
        dispatch(request, object(), outbox)
