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


def test_claim_and_mark_sent(tmp_path):
    db = SQLiteDecisionPersistence(tmp_path / "signals.db")
    try:
        now = _now_text()
        sent_at = (datetime.fromisoformat(now) + timedelta(seconds=30)).isoformat()
        db.persist(_signal_request("key-1", "event-1"))
        claimed = db.claim_pending_outbox(
            now=now,
            lease_seconds=60,
            owner_id="worker-1",
        )
        assert len(claimed) == 1
        assert claimed[0]["status"] == "PROCESSING"
        assert claimed[0]["attempt_count"] == 1
        assert claimed[0]["owner_id"] == "worker-1"
        assert isinstance(claimed[0]["lease_token"], str)
        db.mark_outbox_sent(
            "event-1",
            sent_at=sent_at,
            **_lease_fields(claimed[0]),
        )
        row = db._connection.execute(
            "SELECT status, sent_at, locked_until, owner_id, lease_token FROM outbox WHERE event_id = ?",
            ("event-1",),
        ).fetchone()
        assert row["status"] == "SENT"
        assert row["sent_at"] == sent_at
        assert row["locked_until"] is None
        assert row["owner_id"] is None
        assert row["lease_token"] is None
        assert db.claim_pending_outbox(now=sent_at) == []
    finally:
        db.close()


def test_expired_processing_is_recovered(tmp_path):
    db = SQLiteDecisionPersistence(tmp_path / "signals.db")
    try:
        now = _now_text()
        later = _now_text(60)
        db.persist(_signal_request("key-2", "event-2"))
        claimed = db.claim_pending_outbox(
            now=now,
            lease_seconds=30,
            owner_id="worker-1",
        )
        assert claimed[0]["owner_id"] == "worker-1"
        assert db.recover_expired_processing(now=later) == 1
        row = db._connection.execute(
            "SELECT status, next_attempt_at, locked_until, owner_id, lease_token FROM outbox WHERE event_id = ?",
            ("event-2",),
        ).fetchone()
        assert row["status"] == "RETRY"
        assert row["next_attempt_at"] == later
        assert row["locked_until"] is None
        assert row["owner_id"] is None
        assert row["lease_token"] is None
    finally:
        db.close()


def test_retry_and_dead_letter_transitions_require_exact_lease(tmp_path):
    db = SQLiteDecisionPersistence(tmp_path / "signals.db")
    try:
        now = _now_text()
        later = _now_text(5)
        db.persist(_signal_request("key-3", "event-3"))
        first = db.claim_pending_outbox(
            now=now,
            owner_id="worker-1",
        )[0]
        db.mark_outbox_retry(
            "event-3",
            next_attempt_at=later,
            error="temporary transport failure",
            **_lease_fields(first),
        )

        second = db.claim_pending_outbox(
            now=later,
            owner_id="worker-2",
        )[0]
        with pytest.raises(ValueError, match="lease is invalid"):
            db.mark_outbox_sent(
                "event-3",
                sent_at=(datetime.fromisoformat(later) + timedelta(seconds=1)).isoformat(),
                **_lease_fields(first),
            )

        db.mark_outbox_dead_letter(
            "event-3",
            "permanent transport failure",
            **_lease_fields(second),
        )
        row = db._connection.execute(
            "SELECT status, last_error FROM outbox WHERE event_id = ?",
            ("event-3",),
        ).fetchone()
        assert row["status"] == "DEAD_LETTER"
        assert row["last_error"] == "permanent transport failure"
    finally:
        db.close()


def test_invalid_lifecycle_operations_are_rejected(tmp_path):
    db = SQLiteDecisionPersistence(tmp_path / "signals.db")
    try:
        db.persist(_signal_request("key-4", "event-4"))
        with pytest.raises(TypeError):
            db.mark_outbox_sent("event-4")
        with pytest.raises(ValueError):
            db.claim_pending_outbox(lease_seconds=0)
        with pytest.raises(TypeError):
            db.mark_outbox_retry(
                "event-4",
                "2026-01-01T00:00:00+00:00",
                "temporary",
            )
        with pytest.raises(ValueError):
            db.mark_outbox_retry(
                "event-4",
                "2026-01-01T00:00:00+00:00",
                "",
                owner_id="worker-1",
                lease_token="lease-1",
            )
    finally:
        db.close()
