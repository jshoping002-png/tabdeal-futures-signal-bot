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
from tabdeal_signal.persistence.sqlite import SQLiteDecisionPersistence


def _signal_request(key: str, event_id: str) -> PersistenceRequest:
    context = DecisionContext(
        decision_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        reference_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        snapshot_id="snapshot-1",
        config_version="config-1",
    )
    signal = SignalDecision(
        signal_id=key,
        direction=Direction.LONG,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        snapshot_id="snapshot-1",
        config_version="config-1",
        reason_code="TEST_SIGNAL",
    )
    return PersistenceRequest(
        context=context,
        decision=FinalDecision(status=DecisionStatus.SIGNAL, signal=signal),
        idempotency_key=key,
        event_id=event_id,
    )


def test_claim_and_mark_sent(tmp_path):
    db = SQLiteDecisionPersistence(tmp_path / "signals.db")
    try:
        db.persist(_signal_request("key-1", "event-1"))
        claimed = db.claim_pending_outbox(now="2026-01-01T00:00:00+00:00", lease_seconds=60)
        assert len(claimed) == 1
        assert claimed[0]["status"] == "PROCESSING"
        assert claimed[0]["attempt_count"] == 1
        db.mark_outbox_sent("event-1", sent_at="2026-01-01T00:00:30+00:00")
        row = db._connection.execute(
            "SELECT status, sent_at, locked_until FROM outbox WHERE event_id = ?",
            ("event-1",),
        ).fetchone()
        assert row["status"] == "SENT"
        assert row["sent_at"] == "2026-01-01T00:00:30+00:00"
        assert row["locked_until"] is None
        assert db.claim_pending_outbox(now="2026-01-01T00:01:00+00:00") == []
    finally:
        db.close()


def test_expired_processing_is_recovered(tmp_path):
    db = SQLiteDecisionPersistence(tmp_path / "signals.db")
    try:
        db.persist(_signal_request("key-2", "event-2"))
        db.claim_pending_outbox(now="2026-01-01T00:00:00+00:00", lease_seconds=30)
        assert db.recover_expired_processing(now="2026-01-01T00:01:00+00:00") == 1
        row = db._connection.execute(
            "SELECT status, next_attempt_at, locked_until FROM outbox WHERE event_id = ?",
            ("event-2",),
        ).fetchone()
        assert row["status"] == "RETRY"
        assert row["next_attempt_at"] == "2026-01-01T00:01:00+00:00"
        assert row["locked_until"] is None
    finally:
        db.close()


def test_retry_and_dead_letter_transitions(tmp_path):
    db = SQLiteDecisionPersistence(tmp_path / "signals.db")
    try:
        db.persist(_signal_request("key-3", "event-3"))
        db.claim_pending_outbox(now="2026-01-01T00:00:00+00:00")
        db.mark_outbox_retry(
            "event-3",
            next_attempt_at="2026-01-01T00:05:00+00:00",
            error="temporary transport failure",
        )
        row = db._connection.execute(
            "SELECT status, last_error FROM outbox WHERE event_id = ?", ("event-3",)
        ).fetchone()
        assert row["status"] == "RETRY"
        assert row["last_error"] == "temporary transport failure"

        db.claim_pending_outbox(now="2026-01-01T00:05:00+00:00")
        db.mark_outbox_dead_letter("event-3", "permanent transport failure")
        row = db._connection.execute(
            "SELECT status, last_error FROM outbox WHERE event_id = ?", ("event-3",)
        ).fetchone()
        assert row["status"] == "DEAD_LETTER"
        assert row["last_error"] == "permanent transport failure"
    finally:
        db.close()


def test_invalid_lifecycle_operations_are_rejected(tmp_path):
    db = SQLiteDecisionPersistence(tmp_path / "signals.db")
    try:
        db.persist(_signal_request("key-4", "event-4"))
        with pytest.raises(ValueError):
            db.mark_outbox_sent("event-4")
        with pytest.raises(ValueError):
            db.claim_pending_outbox(lease_seconds=0)
        with pytest.raises(ValueError):
            db.mark_outbox_retry("event-4", "2026-01-01T00:00:00+00:00", "")
    finally:
        db.close()
