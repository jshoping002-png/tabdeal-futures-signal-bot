from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from tabdeal_signal.notification.contracts import (
    NotificationOutcome,
    NotificationRequest,
    NotificationResult,
    NotificationSender,
)
from tabdeal_signal.persistence.outbox import OutboxRepository, OutboxStatus
from tabdeal_signal.persistence.reliability import OutboxLease


@dataclass(frozen=True, slots=True)
class NotificationDispatchResult:
    """Result of one leased outbox delivery attempt and its terminal transition."""

    delivery: NotificationResult
    marked_delivered: bool


def dispatch_outbox_message(
    *,
    request: NotificationRequest,
    sender: NotificationSender,
    outbox: OutboxRepository,
    lease: OutboxLease,
    reference_time: datetime,
) -> NotificationDispatchResult:
    """Deliver one outbox message only while its exact lease is valid."""
    if not isinstance(request, NotificationRequest):
        raise ValueError("request must be a NotificationRequest")
    if not isinstance(lease, OutboxLease):
        raise ValueError("lease must be an OutboxLease")
    if lease.event_id != request.message.event_id:
        raise ValueError("lease event_id must match message event_id")
    if not isinstance(reference_time, datetime):
        raise ValueError("reference_time must be a datetime")
    if reference_time.tzinfo is None:
        raise ValueError("reference_time must be timezone-aware")
    if lease.is_expired_at(reference_time):
        raise ValueError("lease is expired")
    if request.message.status is not OutboxStatus.PENDING:
        raise ValueError("outbox message must be PENDING before delivery")
    if not callable(getattr(sender, "send", None)):
        raise ValueError("sender must provide a callable send method")

    result = sender.send(request)
    if not isinstance(result, NotificationResult):
        raise ValueError("sender must return NotificationResult")

    if result.outcome in (NotificationOutcome.DELIVERED, NotificationOutcome.DUPLICATE):
        outbox.mark_delivered(request.message.event_id, lease)
        return NotificationDispatchResult(delivery=result, marked_delivered=True)

    return NotificationDispatchResult(delivery=result, marked_delivered=False)
