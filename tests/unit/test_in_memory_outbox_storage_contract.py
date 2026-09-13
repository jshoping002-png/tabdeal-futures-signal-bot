from datetime import datetime, timedelta, timezone
from threading import Barrier, Thread

import pytest

from tabdeal_signal.decision.final import FinalDecision
from tabdeal_signal.domain.contracts import DecisionContext, DecisionStatus
from tabdeal_signal.persistence.in_memory_outbox import InMemoryOutboxLeaseRepository, InMemoryOutboxRepository
from tabdeal_signal.persistence.outbox import OutboxMessage, OutboxStatus

UTC = timezone.utc


def make_message(*, event_id: str = "event-1", key: str = "key-1") -> OutboxMessage:
    decision_time = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    context = DecisionContext(decision_time=decision_time, reference_time=datetime(2026, 1, 1, 11, 59, tzinfo=UTC), snapshot_id="snapshot-1", config_version="config-1")
    return OutboxMessage(event_id=event_id, idempotency_key=key, context=context, decision=FinalDecision(DecisionStatus.BLOCKED, reason_code="NO_SIGNAL"), created_at=decision_time)


def test_enqueue_is_idempotent_and_collision_safe() -> None:
    outbox = InMemoryOutboxRepository()
    message = make_message()
    assert outbox.enqueue(message) is True
    assert outbox.enqueue(message) is False
    assert outbox.count() == 1
    with pytest.raises(ValueError, match="idempotency key collision"):
        outbox.enqueue(make_message(event_id="event-2"))


def test_only_exact_current_lease_can_mark_delivered() -> None:
    outbox = InMemoryOutboxRepository()
    leases = InMemoryOutboxLeaseRepository(outbox)
    outbox.enqueue(make_message())
    acquired = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    current = leases.acquire_lease(event_id="event-1", owner_id="worker-1", acquired_at=acquired, expires_at=acquired + timedelta(minutes=1))
    assert current is not None
    stale = type(current)(event_id="event-1", lease_token="stale", owner_id="worker-old", acquired_at=acquired - timedelta(minutes=2), expires_at=acquired - timedelta(minutes=1))
    with pytest.raises(ValueError, match="does not own"):
        outbox.mark_delivered("event-1", stale)
    assert outbox.get("event-1").status is OutboxStatus.PENDING


def test_stale_lease_cannot_release_replacement() -> None:
    outbox = InMemoryOutboxRepository()
    leases = InMemoryOutboxLeaseRepository(outbox)
    outbox.enqueue(make_message())
    acquired = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    first = leases.acquire_lease(event_id="event-1", owner_id="worker-1", acquired_at=acquired, expires_at=acquired + timedelta(seconds=1))
    assert first is not None
    replacement_time = acquired + timedelta(seconds=1)
    second = leases.acquire_lease(event_id="event-1", owner_id="worker-2", acquired_at=replacement_time, expires_at=replacement_time + timedelta(minutes=1))
    assert second is not None
    leases.release_lease(first)
    outbox.mark_delivered("event-1", second)
    assert outbox.get("event-1").status is OutboxStatus.DELIVERED


def test_concurrent_acquisition_has_one_owner() -> None:
    outbox = InMemoryOutboxRepository()
    leases = InMemoryOutboxLeaseRepository(outbox)
    outbox.enqueue(make_message())
    acquired = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    barrier = Barrier(8)
    results = []

    def worker(index: int) -> None:
        barrier.wait()
        results.append(leases.acquire_lease(event_id="event-1", owner_id=f"worker-{index}", acquired_at=acquired, expires_at=acquired + timedelta(minutes=1)))

    threads = [Thread(target=worker, args=(i,)) for i in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert sum(result is not None for result in results) == 1
