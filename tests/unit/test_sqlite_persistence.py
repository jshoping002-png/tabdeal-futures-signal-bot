from datetime import datetime, timedelta, timezone

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


def _request(tmp_path, status=DecisionStatus.BLOCKED, key="k-1", event_id=None):
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
    return PersistenceRequest(
        context=context,
        decision=decision,
        idempotency_key=key,
        event_id=event_id,
    )


def _lease_fields(record):
    return {
        "owner_id": record["owner_id"],
        "lease_token": record["lease_token"],
    }


def _now_text(offset_seconds: int = 0) -> str:
    return (
        datetime.now(timezone.utc).replace(microsecond=0)
        + timedelta(seconds=offset_seconds)
    ).isoformat()


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


class _InterleavingConnection:
    """Proxy that injects a concurrent commit after the preflight read."""

    def __init__(self, connection, interleave):
        self._connection = connection
        self._interleave = interleave
        self._triggered = False

    def execute(self, sql, parameters=()):
        cursor = self._connection.execute(sql, parameters)
        if (
            not self._triggered
            and sql.startswith("SELECT payload_json FROM decisions")
        ):
            self._triggered = True
            self._interleave()
        return cursor

    def __enter__(self):
        self._connection.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb):
        return self._connection.__exit__(exc_type, exc, tb)

    def __getattr__(self, name):
        return getattr(self._connection, name)


def test_concurrent_identical_request_is_idempotent(tmp_path):
    path = tmp_path / "signals.db"
    first = SQLiteDecisionPersistence(path)
    second = SQLiteDecisionPersistence(path)
    request = _request(tmp_path, key="concurrent-key")
    try:
        second.persist(request)
        first._connection.execute(
            "DELETE FROM decisions WHERE idempotency_key = ?", ("concurrent-key",)
        )
        first._connection.commit()

        second.close()
        second = SQLiteDecisionPersistence(path)
        first._connection = _InterleavingConnection(
            first._connection, lambda: second.persist(request)
        )

        result = first.persist(request)

        assert result.persisted is True
        assert result.idempotent_replay is True
        assert first._connection.execute(
            "SELECT COUNT(*) FROM decisions WHERE idempotency_key = ?",
            ("concurrent-key",),
        ).fetchone()[0] == 1
    finally:
        first.close()
        second.close()


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
        request = _request(tmp_path, status=DecisionStatus.SIGNAL, key="signal-key", event_id="event-123")
        db.persist(request)
        assert db._connection.execute("SELECT COUNT(*) FROM decisions").fetchone()[0] == 1
        assert db._connection.execute("SELECT COUNT(*) FROM outbox").fetchone()[0] == 1
        row = db._connection.execute(
            "SELECT event_id FROM outbox WHERE idempotency_key = ?", ("signal-key",)
        ).fetchone()
        assert row["event_id"] == "event-123"
    finally:
        db.close()


def test_signal_without_event_id_uses_deterministic_fallback(tmp_path):
    db = SQLiteDecisionPersistence(tmp_path / "signals.db")
    try:
        request = _request(tmp_path, status=DecisionStatus.SIGNAL, key="fallback-signal-key")
        first = db.persist(request)
        second = db.persist(request)
        assert first.persisted is True
        assert second.persisted is True
        assert second.idempotent_replay is True
        rows = db._connection.execute(
            "SELECT event_id FROM outbox WHERE idempotency_key = ?", ("fallback-signal-key",)
        ).fetchall()
        assert len(rows) == 1
        assert rows[0]["event_id"] == "signal:fallback-signal-key"
    finally:
        db.close()


def test_outbox_failure_rolls_back_decision(tmp_path):
    db = SQLiteDecisionPersistence(tmp_path / "signals.db")
    try:
        db.persist(_request(tmp_path, status=DecisionStatus.SIGNAL, key="first-signal", event_id="shared-event"))
        with pytest.raises(PersistenceCollisionError):
            db.persist(_request(tmp_path, status=DecisionStatus.SIGNAL, key="second-signal", event_id="shared-event"))
        assert db._connection.execute("SELECT COUNT(*) FROM decisions").fetchone()[0] == 1
        assert db._connection.execute("SELECT COUNT(*) FROM outbox").fetchone()[0] == 1
        assert db._connection.execute(
            "SELECT COUNT(*) FROM decisions WHERE idempotency_key = ?", ("second-signal",)
        ).fetchone()[0] == 0
    finally:
        db.close()


def test_quarantine_outbox_record_dead_letters_claimed_row(tmp_path):
    db = SQLiteDecisionPersistence(tmp_path / "signals.db")
    try:
        db.persist(_request(tmp_path, status=DecisionStatus.SIGNAL, key="quarantine-key", event_id="quarantine-event"))
        now = _now_text()
        claimed = db.claim_pending_outbox(
            now=now, lease_seconds=60, limit=1, owner_id="worker-1"
        )
        assert len(claimed) == 1
        internal_id = claimed[0]["internal_id"]
        db.quarantine_outbox_record(
            internal_id,
            "invalid event_id: missing or non-string",
            **_lease_fields(claimed[0]),
        )
        row = db._connection.execute(
            "SELECT status, last_error, locked_until FROM outbox WHERE rowid = ?", (internal_id,)
        ).fetchone()
        assert row["status"] == "DEAD_LETTER"
        assert row["last_error"] == "invalid event_id: missing or non-string"
        assert row["locked_until"] is None
    finally:
        db.close()


def test_expired_processing_lease_returns_record_to_retry(tmp_path):
    db = SQLiteDecisionPersistence(tmp_path / "signals.db")
    try:
        db.persist(_request(tmp_path, status=DecisionStatus.SIGNAL, key="lease-key", event_id="lease-event"))
        claimed = db.claim_pending_outbox(now="2026-01-01T00:00:00+00:00", lease_seconds=60, limit=1)
        assert len(claimed) == 1
        assert claimed[0]["status"] == "PROCESSING"
        recovered = db.recover_expired_processing(now="2026-01-01T00:01:00+00:00")
        assert recovered == 1
        row = db._connection.execute(
            "SELECT status, next_attempt_at, locked_until, last_error FROM outbox WHERE event_id = ?",
            ("lease-event",),
        ).fetchone()
        assert row["status"] == "RETRY"
        assert row["next_attempt_at"] == "2026-01-01T00:01:00+00:00"
        assert row["locked_until"] is None
        assert row["last_error"] == "lease expired"
    finally:
        db.close()


def test_sent_outbox_record_is_not_claimed_again(tmp_path):
    db = SQLiteDecisionPersistence(tmp_path / "signals.db")
    try:
        db.persist(_request(tmp_path, status=DecisionStatus.SIGNAL, key="sent-key", event_id="sent-event"))
        now = _now_text()
        sent_at = (datetime.fromisoformat(now) + timedelta(seconds=30)).isoformat()
        claimed = db.claim_pending_outbox(
            now=now, lease_seconds=60, limit=1, owner_id="worker-1"
        )
        assert len(claimed) == 1
        db.mark_outbox_sent(
            "sent-event",
            sent_at=sent_at,
            **_lease_fields(claimed[0]),
        )
        assert db.claim_pending_outbox(now=sent_at, limit=1) == []
        row = db._connection.execute(
            "SELECT status, sent_at, locked_until FROM outbox WHERE event_id = ?",
            ("sent-event",),
        ).fetchone()
        assert row["status"] == "SENT"
        assert row["sent_at"] == sent_at
        assert row["locked_until"] is None
    finally:
        db.close()
