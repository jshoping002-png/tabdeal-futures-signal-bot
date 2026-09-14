from datetime import datetime, timezone

import pytest

from tabdeal_signal.decision.final import FinalDecision
from tabdeal_signal.domain.contracts import (
    DecisionContext,
    DecisionStatus,
    Direction,
    SignalDecision,
)
from tabdeal_signal.persistence.contracts import PersistenceRequest
from tabdeal_signal.persistence.sqlite import (
    PersistenceCollisionError,
    SQLiteDecisionPersistence,
)


def _request(tmp_path, status=DecisionStatus.BLOCKED, key="k-1"):
    context = DecisionContext(
        decision_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        reference_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        snapshot_id="snapshot-1",
        config_version="config-1",
    )
    if status is DecisionStatus.SIGNAL:
        signal = SignalDecision(
            signal_id="signal-1",
            direction=Direction.LONG,
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            snapshot_id="snapshot-1",
            config_version="config-1",
            reason_code="TEST_SIGNAL",
        )
        decision = FinalDecision(status=status, signal=signal)
    else:
        decision = FinalDecision(status=status, reason_code="TEST_BLOCK")
    return PersistenceRequest(context=context, decision=decision, idempotency_key=key)


def test_blocked_is_persisted_without_outbox(tmp_path):
    db = SQLiteDecisionPersistence(tmp_path / "signals.db")
    try:
        result = db.persist(_request(tmp_path))
        assert result.persisted is True
        assert db._connection.execute("SELECT COUNT(*) FROM decisions").fetchone()[0] == 1
        assert db._connection.execute("SELECT COUNT(*) FROM outbox").fetchone()[0] == 0
    finally:
        db.close()


def test_replay_is_idempotent(tmp_path):
    db = SQLiteDecisionPersistence(tmp_path / "signals.db")
    try:
        request = _request(tmp_path)
        assert db.persist(request).persisted is True
        result = db.persist(request)
        assert result.persisted is True
        assert result.idempotent_replay is True
        assert db._connection.execute("SELECT COUNT(*) FROM decisions").fetchone()[0] == 1
    finally:
        db.close()


def test_collision_is_rejected(tmp_path):
    db = SQLiteDecisionPersistence(tmp_path / "signals.db")
    try:
        db.persist(_request(tmp_path, key="same-key"))
        with pytest.raises(PersistenceCollisionError):
            db.persist(
                PersistenceRequest(
                    context=_request(tmp_path, key="same-key").context,
                    decision=FinalDecision(
                        status=DecisionStatus.BLOCKED,
                        reason_code="DIFFERENT",
                    ),
                    idempotency_key="same-key",
                )
            )
    finally:
        db.close()


def test_signal_creates_outbox(tmp_path):
    db = SQLiteDecisionPersistence(tmp_path / "signals.db")
    try:
        request = _request(tmp_path, status=DecisionStatus.SIGNAL, key="signal-key")
        db.persist(request)
        assert db._connection.execute("SELECT COUNT(*) FROM decisions").fetchone()[0] == 1
        assert db._connection.execute("SELECT COUNT(*) FROM outbox").fetchone()[0] == 1
    finally:
        db.close()
