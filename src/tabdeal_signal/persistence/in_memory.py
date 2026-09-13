from __future__ import annotations

from dataclasses import dataclass
from threading import Lock

from tabdeal_signal.persistence.contracts import PersistenceRequest, PersistenceResult


@dataclass(frozen=True, slots=True)
class PersistedDecision:
    """In-memory audit record used for deterministic contract verification."""

    request: PersistenceRequest


class InMemoryDecisionPersistence:
    """Atomic/idempotent reference implementation for tests and verification.

    This is intentionally not a production storage adapter. Its purpose is to
    make the persistence contract executable without introducing a database
    vendor or deployment decision.
    """

    def __init__(self) -> None:
        self._lock = Lock()
        self._records: dict[str, PersistedDecision] = {}

    def persist(self, request: PersistenceRequest) -> PersistenceResult:
        if not isinstance(request, PersistenceRequest):
            raise ValueError("request must be a PersistenceRequest")

        with self._lock:
            existing = self._records.get(request.idempotency_key)
            if existing is not None:
                if existing.request != request:
                    raise ValueError("idempotency key collision")
                return PersistenceResult(persisted=True, idempotent_replay=True)

            self._records[request.idempotency_key] = PersistedDecision(request=request)
            return PersistenceResult(persisted=True)

    def get(self, idempotency_key: str) -> PersistedDecision | None:
        with self._lock:
            return self._records.get(idempotency_key)

    def count(self) -> int:
        with self._lock:
            return len(self._records)
