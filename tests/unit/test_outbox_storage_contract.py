from datetime import datetime, timedelta, timezone

from tabdeal_signal.decision.final import FinalDecision
from tabdeal_signal.domain.contracts import DecisionContext, DecisionStatus
from tabdeal_signal.persistence.outbox import OutboxMessage, OutboxRepository, OutboxStatus
from tabdeal_signal.persistence.reliability import OutboxLease, OutboxLeaseRepository


class ContractOutbox:
    """Minimal in-memory model used only to exercise repository semantics."""

    def __init__(self) -> None:
        self.messages = {}
        self.leases = {}

    def enqueue(self, message: OutboxMessage) -> bool:
        existing = self.messages.get(message.idempotency_key)
        if existing is not None:
            if existing != message:
                raise ValueError("idempotency key collision")
            return False
        self.messages[message.idempotency_key] = message
        return True

    def mark_delivered(self, event_id: str, lease: OutboxLease) -> None:
        message = next(
            (value for value in self.messages.values() if value.event_id == event_id),
            None,
        )
        if message is None:
            return
        current = self.leases.get(event_id)
        if current != lease:
            return
        self.messages[message.idempotency_key] = OutboxMessage(
            event_id=message.event_id,
            idempotency_key=message.idempotency_key,
            context=message.context,
            decision=message.decision,
            created_at=message.created_at,
            status=OutboxStatus.DELIVERED,
        )

    def acquire_lease(
        self,
        *,
        event_id: str,
        owner_id: str,
        lease_token: str,
        acquired_at: datetime,
        expires_at: datetime,
    ) -> OutboxLease | None:
        current = self.leases.get(event_id)
        if current is not None and not current.is_expired_at(acquired_at):
            return None
        lease = OutboxLease(
            event_id=event_id,
            lease_token=lease_token,
            owner_id=owner_id,
            acquired_at=acquired_at,
            expires_at=expires_at,
        )
        self.leases[event_id] = lease
        return lease

    def release_lease(self, lease: OutboxLease) -> None:
        if self.leases.get(lease.event_id) == lease:
            del self.leases[lease.event_id]


def make_message(*, idempotency_key: str = "idem-1") -> OutboxMessage:
    decision_time = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    context = DecisionContext(
        decision_time=decision_time,
        reference_time=decision_time,
        snapshot_id="snapshot-1",
        config_version="v1",
    )
    return OutboxMessage(
        event_id="event-1",
        idempotency_key=idempotency_key,
        context=context,
        decision=FinalDecision(status=DecisionStatus.BLOCKED, reason_code="NO_SIGNAL"),
        created_at=decision_time,
    )


def make_lease(*, token: str = "lease-1", owner: str = "worker-1") -> OutboxLease:
    acquired_at = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    return OutboxLease(
        event_id="event-1",
        lease_token=token,
        owner_id=owner,
        acquired_at=acquired_at,
        expires_at=acquired_at + timedelta(minutes=1),
    )


def test_repository_protocol_exposes_required_boundaries() -> None:
    assert hasattr(OutboxRepository, "enqueue")
    assert hasattr(OutboxRepository, "mark_delivered")
    assert hasattr(OutboxLeaseRepository, "acquire_lease")
    assert hasattr(OutboxLeaseRepository, "release_lease")


def test_enqueue_persists_new_message_once() -> None:
    repository = ContractOutbox()
    message = make_message()

    assert repository.enqueue(message) is True
    assert repository.messages[message.idempotency_key] == message


def test_enqueue_same_idempotency_key_does_not_create_duplicate() -> None:
    repository = ContractOutbox()
    first = make_message()
    second = make_message()

    assert repository.enqueue(first) is True
    assert repository.enqueue(second) is False
    assert len(repository.messages) == 1
    assert repository.messages[first.idempotency_key] == first


def test_enqueue_idempotency_key_collision_fails_closed() -> None:
    repository = ContractOutbox()
    first = make_message()
    conflicting = OutboxMessage(
        event_id=first.event_id,
        idempotency_key=first.idempotency_key,
        context=first.context,
        decision=FinalDecision(
            status=DecisionStatus.BLOCKED,
            reason_code="DIFFERENT_REASON",
        ),
        created_at=first.created_at,
    )

    assert repository.enqueue(first) is True
    try:
        repository.enqueue(conflicting)
    except ValueError as exc:
        assert str(exc) == "idempotency key collision"
    else:
        raise AssertionError("idempotency collision must fail closed")
    assert len(repository.messages) == 1
    assert repository.messages[first.idempotency_key] == first


def test_concurrent_lease_acquisition_is_exclusive() -> None:
    repository = ContractOutbox()
    acquired_at = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    expires_at = acquired_at + timedelta(minutes=1)

    first = repository.acquire_lease(
        event_id="event-1",
        owner_id="worker-1",
        lease_token="lease-1",
        acquired_at=acquired_at,
        expires_at=expires_at,
    )
    second = repository.acquire_lease(
        event_id="event-1",
        owner_id="worker-2",
        lease_token="lease-2",
        acquired_at=acquired_at,
        expires_at=expires_at,
    )

    assert first is not None
    assert second is None


def test_mark_delivered_requires_exact_current_lease() -> None:
    repository = ContractOutbox()
    message = make_message()
    repository.enqueue(message)
    current = repository.acquire_lease(
        event_id="event-1",
        owner_id="worker-1",
        lease_token="lease-1",
        acquired_at=message.created_at,
        expires_at=message.created_at + timedelta(minutes=1),
    )
    stale = make_lease(token="old-token", owner="old-worker")

    assert current is not None
    repository.mark_delivered(message.event_id, stale)
    assert repository.messages[message.idempotency_key].status is OutboxStatus.PENDING

    repository.mark_delivered(message.event_id, current)
    assert repository.messages[message.idempotency_key].status is OutboxStatus.DELIVERED


def test_stale_lease_cannot_release_replacement_ownership() -> None:
    repository = ContractOutbox()
    first = make_lease()
    repository.leases[first.event_id] = first
    repository.leases[first.event_id] = make_lease(token="lease-2", owner="worker-2")

    repository.release_lease(first)

    assert repository.leases[first.event_id].lease_token == "lease-2"


def test_exact_lease_can_be_released() -> None:
    repository = ContractOutbox()
    lease = make_lease()
    repository.leases[lease.event_id] = lease

    repository.release_lease(lease)

    assert lease.event_id not in repository.leases
