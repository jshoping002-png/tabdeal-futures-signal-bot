from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from tabdeal_signal.persistence.outbox import OutboxMessage


class NotificationOutcome(str, Enum):
    DELIVERED = "DELIVERED"
    DUPLICATE = "DUPLICATE"
    RETRYABLE = "RETRYABLE"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class NotificationRequest:
    """Explicit delivery input for one immutable outbox message."""

    message: OutboxMessage

    def __post_init__(self) -> None:
        if not isinstance(self.message, OutboxMessage):
            raise ValueError("message must be an OutboxMessage")


@dataclass(frozen=True, slots=True)
class NotificationResult:
    """Transport-neutral result of one delivery attempt."""

    outcome: NotificationOutcome
    reason_code: str

    def __post_init__(self) -> None:
        if not isinstance(self.outcome, NotificationOutcome):
            raise ValueError("outcome must be a NotificationOutcome")
        if not isinstance(self.reason_code, str) or not self.reason_code.strip():
            raise ValueError("reason_code is required")

    @property
    def retryable(self) -> bool:
        return self.outcome is NotificationOutcome.RETRYABLE


class NotificationSender(Protocol):
    """Delivery boundary; transport and retry policy stay outside the contract."""

    def send(self, request: NotificationRequest) -> NotificationResult:
        ...
