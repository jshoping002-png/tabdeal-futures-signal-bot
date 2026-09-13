from datetime import datetime, timezone
from threading import Barrier, Thread

import pytest

from tabdeal_signal.decision.final import FinalDecision
from tabdeal_signal.domain.contracts import DecisionContext, DecisionStatus
from tabdeal_signal.persistence.contracts import PersistenceRequest, PersistenceResult
from tabdeal_signal.persistence.in_memory import InMemoryDecisionPersistence


UTC = timezone.utc


def context() -> DecisionContext:
    return DecisionContext(
        decision_time=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
        reference_time=datetime(2026, 1, 1, 11, 59, tzinfo=UTC),
        snapshot_id="snapshot-1",
        config_version="config-1",
    )


def blocked_decision() -> FinalDecision:
    return FinalDecision(DecisionStatus.BLOCKED, reason_code="NO_SIGNAL")


def request(key: str = "snapshot-1:decision-1") -> PersistenceRequest:
    return PersistenceRequest(context=context(), decision=blocked_decision(), idempotency_key=key)


def test_persistence_request_requires_explicit_idempotency_key() -> None:
    with pytest.raises(ValueError, match="idempotency_key is required"):
        PersistenceRequest(context=context(), decision=blocked_decision(), idempotency_key=" ")


def test_persistence_request_rejects_invalid_context() -> None:
    with pytest.raises(ValueError, match="context must be a DecisionContext"):
        PersistenceRequest(context="invalid", decision=blocked_decision(), idempotency_key="key")


def test_persistence_request_rejects_invalid_decision() -> None:
    with pytest.raises(ValueError, match="decision must be a FinalDecision"):
        PersistenceRequest(context=context(), decision="invalid", idempotency_key="key")


def test_persistence_request_keeps_context_and_decision_together() -> None:
    persisted = request()
    assert persisted.context.snapshot_id == "snapshot-1"
    assert persisted.decision.status is DecisionStatus.BLOCKED
    assert persisted.idempotency_key == "snapshot-1:decision-1"


def test_persistence_result_rejects_non_persisted_replay() -> None:
    with pytest.raises(ValueError, match="idempotent replay must be persisted"):
        PersistenceResult(persisted=False, idempotent_replay=True)


def test_persistence_result_rejects_non_boolean_persisted() -> None:
    with pytest.raises(ValueError, match="persisted must be a bool"):
        PersistenceResult(persisted="yes")


def test_persistence_result_rejects_non_boolean_replay_flag() -> None:
    with pytest.raises(ValueError, match="idempotent_replay must be a bool"):
        PersistenceResult(persisted=True, idempotent_replay="yes")


def test_persistence_result_accepts_new_persistence() -> None:
    result = PersistenceResult(persisted=True)
    assert result.persisted is True
    assert result.idempotent_replay is False


def test_persistence_result_accepts_idempotent_replay() -> None:
    result = PersistenceResult(persisted=True, idempotent_replay=True)
    assert result.persisted is True
    assert result.idempotent_replay is True


def test_in_memory_persistence_is_idempotent() -> None:
    store = InMemoryDecisionPersistence()
    first = store.persist(request())
    second = store.persist(request())

    assert first == PersistenceResult(persisted=True)
    assert second == PersistenceResult(persisted=True, idempotent_replay=True)
    assert store.count() == 1


def test_in_memory_persistence_rejects_idempotency_collision() -> None:
    store = InMemoryDecisionPersistence()
    store.persist(request())
    changed_context = DecisionContext(
        decision_time=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
        reference_time=datetime(2026, 1, 1, 11, 58, tzinfo=UTC),
        snapshot_id="snapshot-2",
        config_version="config-1",
    )
    collision = PersistenceRequest(
        context=changed_context,
        decision=blocked_decision(),
        idempotency_key="snapshot-1:decision-1",
    )
    with pytest.raises(ValueError, match="idempotency key collision"):
        store.persist(collision)


def test_in_memory_persistence_converges_concurrent_duplicates() -> None:
    store = InMemoryDecisionPersistence()
    barrier = Barrier(8)
    results: list[PersistenceResult] = []

    def worker() -> None:
        barrier.wait()
        results.append(store.persist(request("same-key")))

    threads = [Thread(target=worker) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(results) == 8
    assert sum(result.idempotent_replay for result in results) == 7
    assert store.count() == 1
