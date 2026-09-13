from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol

from tabdeal_signal.decision.final import FinalDecision
from tabdeal_signal.domain.contracts import DecisionContext


class OutboxStatus(str, Enum):
    PENDING = "PENDING"
    DELIVERED = "DELIVERED"


@dataclass(frozen=True, slots=True)
class OutboxMessage:
    """Immutable notification intent created by atomic persistence."""

    event_id: str
    idempotency_key: str
    context: DecisionContext
    decision: FinalDecision
    created_at: datetime
    status: OutboxStatus = OutboxStatus.PENDING

    def __post_init__(self) -> None:
        if not isinstance(self.event_id, str) or not self.event_id.strip():
            raise ValueError("event_id is required")
        if not isinstance(self.idempotency_key, str) or not self.idempotency_key.strip():
            raise ValueError("idempotency_key is required")
        if not isinstance(self.context, DecisionContext):
            raise ValueError("context must be a DecisionContext")
        if not isinstance(self.decision, FinalDecision):
            raise ValueError("decision must be a FinalDecision")
        if not isinstance(self.created_at, datetime):
            raise ValueError("created_at must be a datetime")
        if self.created_at.tzinfo is None or self.created_at.tzinfo != self.context.decision_time.tzinfo:
            raise ValueError("created_at must use the context timezone")
        if not isinstance(self.status, OutboxStatus):
            raise ValueError("status must be an OutboxStatus")


class OutboxRepository(Protocol):
    """Storage boundary; implementations must enforce atomic insert/idempotency."""

    def enqueue(self, message: OutboxMessage) -> bool:
        """Persist once; return False only when the same idempotency key already exists."""
        ...

    def mark_delivered(self, event_id: str) -> None:
        """Mark an existing message delivered without creating a duplicate event."""
        ...
