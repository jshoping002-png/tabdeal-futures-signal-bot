from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from tabdeal_signal.decision.final import FinalDecision
from tabdeal_signal.domain.contracts import DecisionContext


@dataclass(frozen=True, slots=True)
class PersistenceRequest:
    """Explicit input for one atomic decision-persistence operation."""

    context: DecisionContext
    decision: FinalDecision
    idempotency_key: str
    event_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.context, DecisionContext):
            raise ValueError("context must be a DecisionContext")
        if not isinstance(self.decision, FinalDecision):
            raise ValueError("decision must be a FinalDecision")
        if not isinstance(self.idempotency_key, str) or not self.idempotency_key.strip():
            raise ValueError("idempotency_key is required")
        if self.event_id is not None and (
            not isinstance(self.event_id, str) or not self.event_id.strip()
        ):
            raise ValueError("event_id must be a non-empty string when provided")


@dataclass(frozen=True, slots=True)
class PersistenceResult:
    """Outcome of an atomic persistence attempt."""

    persisted: bool
    idempotent_replay: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.persisted, bool):
            raise ValueError("persisted must be a bool")
        if not isinstance(self.idempotent_replay, bool):
            raise ValueError("idempotent_replay must be a bool")
        if self.idempotent_replay and not self.persisted:
            raise ValueError("idempotent replay must be persisted")


class DecisionPersistence(Protocol):
    """Atomic, idempotent persistence boundary for final decisions.

    Implementations must persist the decision and any associated signal/outbox
    state as one transaction. Repeating the same idempotency key must not create
    a duplicate logical decision. Storage technology and schema are deliberately
    left unspecified until their contract is defined.
    """

    def persist(self, request: PersistenceRequest) -> PersistenceResult:
        ...
