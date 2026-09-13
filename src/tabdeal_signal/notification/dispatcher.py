from __future__ import annotations

from dataclasses import dataclass

from tabdeal_signal.notification.contracts import (
    NotificationOutcome,
    NotificationRequest,
    NotificationResult,
    NotificationSender,
)
from tabdeal_signal.persistence.outbox import OutboxRepository


@dataclass(frozen=True, slots=True)
class NotificationDispatchResult:
    """Result of one outbox delivery attempt and its terminal state transition."""

    delivery: NotificationResult
    marked_delivered: bool


def dispatch_outbox_message(
    *,
    request: NotificationRequest,
    sender: NotificationSender,
    outbox: OutboxRepository,
) -> NotificationDispatchResult:
    """Deliver one outbox message without inventing transport or retry policy.

    Only successful or duplicate delivery is terminal and therefore marks the
    outbox message delivered. Retryable and blocked outcomes remain untouched so
    a separately defined retry/recovery policy can decide what happens next.
    """
    if not isinstance(request, NotificationRequest):
        raise ValueError("request must be a NotificationRequest")

    result = sender.send(request)
    if not isinstance(result, NotificationResult):
        raise ValueError("sender must return NotificationResult")

    if result.outcome in (NotificationOutcome.DELIVERED, NotificationOutcome.DUPLICATE):
        outbox.mark_delivered(request.message.event_id)
        return NotificationDispatchResult(delivery=result, marked_delivered=True)

    return NotificationDispatchResult(delivery=result, marked_delivered=False)
