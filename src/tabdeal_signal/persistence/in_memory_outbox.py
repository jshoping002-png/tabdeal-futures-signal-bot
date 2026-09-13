from __future__ import annotations

from datetime import datetime
from threading import RLock

from tabdeal_signal.persistence.outbox import OutboxMessage, OutboxRepository, OutboxStatus
from tabdeal_signal.persistence.reliability import OutboxLease, OutboxLeaseRepository


class InMemoryOutboxRepository(OutboxRepository):
    """Reference outbox storage for deterministic tests; not production storage."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._messages: dict[str, OutboxMessage] = {}
        self._leases: dict[str, OutboxLease] = {}
        self._lease_sequence = 0

    def enqueue(self, message: OutboxMessage) -> bool:
        if not isinstance(message, OutboxMessage):
            raise ValueError("message must be an OutboxMessage")
        with self._lock:
            existing = self._messages.get(message.idempotency_key)
            if existing is not None:
                if existing != message:
                    raise ValueError("idempotency key collision")
                return False
            self._messages[message.idempotency_key] = message
            return True

    def mark_delivered(self, event_id: str, lease: OutboxLease) -> None:
        if not isinstance(event_id, str) or not event_id.strip():
            raise ValueError("event_id is required")
        if not isinstance(lease, OutboxLease):
            raise ValueError("lease must be an OutboxLease")
        if lease.event_id != event_id:
            raise ValueError("lease event_id must match event_id")
        with self._lock:
            current_lease = self._leases.get(event_id)
            if current_lease != lease:
                raise ValueError("lease does not own event")
            message_key = next(
                (key for key, value in self._messages.items() if value.event_id == event_id),
                None,
            )
            if message_key is None:
                raise ValueError("event_id not found")
            message = self._messages[message_key]
            if message.status is OutboxStatus.DELIVERED:
                return
            self._messages[message_key] = OutboxMessage(
                event_id=message.event_id,
                idempotency_key=message.idempotency_key,
                context=message.context,
                decision=message.decision,
                created_at=message.created_at,
                status=OutboxStatus.DELIVERED,
            )
            del self._leases[event_id]

    def get(self, event_id: str) -> OutboxMessage | None:
        with self._lock:
            return next((m for m in self._messages.values() if m.event_id == event_id), None)

    def count(self) -> int:
        with self._lock:
            return len(self._messages)


class InMemoryOutboxLeaseRepository(OutboxLeaseRepository):
    """Reference exclusive lease storage for deterministic tests; not production storage."""

    def __init__(self, outbox: InMemoryOutboxRepository) -> None:
        self._outbox = outbox

    def acquire_lease(
        self,
        *,
        event_id: str,
        owner_id: str,
        acquired_at: datetime,
        expires_at: datetime,
    ) -> OutboxLease | None:
        if not isinstance(event_id, str) or not event_id.strip():
            raise ValueError("event_id is required")
        if not isinstance(owner_id, str) or not owner_id.strip():
            raise ValueError("owner_id is required")
        candidate = OutboxLease(
            event_id=event_id,
            lease_token=self._next_token(),
            owner_id=owner_id,
            acquired_at=acquired_at,
            expires_at=expires_at,
        )
        with self._outbox._lock:
            if self._outbox.get(event_id) is None:
                raise ValueError("event_id not found")
            existing = self._outbox._leases.get(event_id)
            if existing is not None and acquired_at < existing.expires_at:
                return None
            self._outbox._leases[event_id] = candidate
            return candidate

    def release_lease(self, lease: OutboxLease) -> None:
        if not isinstance(lease, OutboxLease):
            raise ValueError("lease must be an OutboxLease")
        with self._outbox._lock:
            current = self._outbox._leases.get(lease.event_id)
            if current != lease:
                return
            del self._outbox._leases[lease.event_id]

    def _next_token(self) -> str:
        with self._outbox._lock:
            self._outbox._lease_sequence += 1
            return f"lease-{self._outbox._lease_sequence}"
