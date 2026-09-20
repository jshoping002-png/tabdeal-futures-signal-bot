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
from tabdeal_signal.persistence.sqlite import PersistenceCollisionError, SQLiteDecisionPersistence


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


class _InterleavingConnection:
    def __init__(self, connection, interleave):
        self._connection = connection
        self._interleave = interleave
        self._triggered = False

    def execute(self, sql, parameters=()):
        cursor = self._connection.execute(sql, parameters)
        if not self._triggered and sql.lstrip().startswith("SELECT rowid AS internal_id FROM outbox"):
            return _InterleavingCursor(cursor, self._interleave, self)
        return cursor

    def __enter__(self):
        self._connection.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb):
        return self._connection.__exit__(exc_type, exc, tb)

    def __getattr__(self, name):
        return getattr(self._connection, name)


class _InterleavingCursor:
    def __init__(self, cursor, interleave, owner):
        self._cursor = cursor
        self._interleave = interleave
        self._owner = owner

    def fetchall(self):
        rows = self._cursor.fetchall()
        if not self._owner._triggered:
            self._owner._triggered = True
            self._owner._connection.commit()
            self._interleave()
        return rows

    def __getattr__(self, name):
        return getattr(self._cursor, name)


def test_claim_is_exclusive_when_another_worker_wins_between_select_and_update(tmp_path):
    path = tmp_path / "signals.db"
    first = SQLiteDecisionPersistence(path)
    second = SQLiteDecisionPersistence(path)
    try:
        first.persist(_signal_request("key-race", "event-race"))
        second_claimed = []
        first._connection = _InterleavingConnection(
            first._connection,
            lambda: second_claimed.extend(
                second.claim_pending_outbox(
                    now="2026-01-01T00:00:00+00:00",
                    owner_id="worker-2",
                )
            ),
        )
        assert first.claim_pending_outbox(
            now="2026-01-01T00:00:00+00:00",
            owner_id="worker-1",
        ) == []
        assert len(second_claimed) == 1
        row = first._connection.execute(
            "SELECT status, owner_id FROM outbox WHERE event_id = ?",
            ("event-race",),
        ).fetchone()
        assert row["status"] == "PROCESSING"
        assert row["owner_id"] == "worker-2"
    finally:
        first.close()
        second.close()


def test_lifecycle_timestamps_are_stored_as_utc(tmp_path):
    db = SQLiteDecisionPersistence(tmp_path / "signals.db")
    try:
        db.persist(_signal_request("key-time", "event-time"))
        now = datetime.now(timezone.utc).replace(microsecond=0)
        local_tz = timezone(timedelta(hours=3))
        local_now = now.astimezone(local_tz).isoformat()
        claimed = db.claim_pending_outbox(
            now=local_now,
            lease_seconds=60,
            owner_id="worker-1",
        )[0]
        assert claimed["updated_at"] == now.isoformat()
        assert claimed["locked_until"] == (now + timedelta(seconds=60)).isoformat()
        retry_at = now + timedelta(minutes=5)
        retry_local = retry_at.astimezone(timezone(timedelta(hours=4))).isoformat()
        db.mark_outbox_retry(
            "event-time",
            next_attempt_at=retry_local,
            error="temporary",
            **_lease_fields(claimed),
        )
        row = db._connection.execute(
            "SELECT next_attempt_at FROM outbox WHERE event_id = ?",
            ("event-time",),
        ).fetchone()
        assert row["next_attempt_at"] == retry_at.isoformat()
    finally:
        db.close()


def test_invalid_lifecycle_timestamps_are_rejected(tmp_path):
    db = SQLiteDecisionPersistence(tmp_path / "signals.db")
    try:
        db.persist(_signal_request("key-invalid-time", "event-invalid-time"))
        with pytest.raises(ValueError, match="timezone-aware"):
            db.claim_pending_outbox(
                now="2026-01-01T00:00:00",
                owner_id="worker-1",
            )
        claimed = db.claim_pending_outbox(
            now=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            owner_id="worker-1",
        )[0]
        with pytest.raises(ValueError, match="timezone-aware"):
            db.mark_outbox_retry(
                "event-invalid-time",
                next_attempt_at="2026-01-01T00:05:00",
                error="temporary",
                **_lease_fields(claimed),
            )
    finally:
        db.close()


def test_non_string_lifecycle_error_is_rejected(tmp_path):
    db = SQLiteDecisionPersistence(tmp_path / "signals.db")
    try:
        db.persist(_signal_request("key-error-type", "event-error-type"))
        claimed = db.claim_pending_outbox(
            now=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            owner_id="worker-1",
        )[0]
        with pytest.raises(ValueError, match="non-empty string"):
            db.mark_outbox_retry(
                "event-error-type",
                next_attempt_at=(datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
                error=None,
                **_lease_fields(claimed),
            )
    finally:
        db.close()


def test_dead_letter_and_quarantine_validate_input_types(tmp_path):
    db = SQLiteDecisionPersistence(tmp_path / "signals.db")
    try:
        db.persist(_signal_request("key-validation-1", "event-validation-1"))
        claimed = db.claim_pending_outbox(now=_now_text(), owner_id="worker-1")[0]
        with pytest.raises(ValueError, match="non-empty string"):
            db.mark_outbox_dead_letter("event-validation-1", None, **_lease_fields(claimed))
        with pytest.raises(ValueError, match="positive integer"):
            db.quarantine_outbox_record(True, "bad id", **_lease_fields(claimed))
    finally:
        db.close()


def test_lifecycle_mutations_reject_blank_event_ids(tmp_path):
    db = SQLiteDecisionPersistence(tmp_path / "signals.db")
    try:
        db.persist(_signal_request("key-validation-2", "event-validation-2"))
        claimed = db.claim_pending_outbox(now=_now_text(), owner_id="worker-1")[0]
        with pytest.raises(ValueError, match="event_id must be a non-empty string"):
            db.mark_outbox_sent("", **_lease_fields(claimed))
    finally:
        db.close()


def test_claim_rejects_boolean_or_non_integer_limits(tmp_path):
    db = SQLiteDecisionPersistence(tmp_path / "signals.db")
    try:
        with pytest.raises(ValueError, match="positive integers"):
            db.claim_pending_outbox(lease_seconds=True)
        with pytest.raises(ValueError, match="positive integers"):
            db.claim_pending_outbox(limit=True)
        with pytest.raises(ValueError, match="positive integers"):
            db.claim_pending_outbox(lease_seconds=1.5)
    finally:
        db.close()


def test_signal_replay_requires_complete_outbox_state(tmp_path):
    db = SQLiteDecisionPersistence(tmp_path / "signals.db")
    try:
        request = _signal_request("key-replay-integrity", "event-replay-integrity")
        db.persist(request)
        db._connection.execute("DELETE FROM outbox WHERE idempotency_key = ?", (request.idempotency_key,))
        db._connection.commit()
        with pytest.raises(PersistenceCollisionError, match="missing outbox"):
            db.persist(request)
    finally:
        db.close()


def test_signal_replay_rejects_inconsistent_outbox_payload(tmp_path):
    db = SQLiteDecisionPersistence(tmp_path / "signals.db")
    try:
        request = _signal_request("key-replay-payload", "event-replay-payload")
        db.persist(request)
        db._connection.execute("UPDATE outbox SET payload_json = ? WHERE idempotency_key = ?", ("{}", request.idempotency_key))
        db._connection.commit()
        with pytest.raises(PersistenceCollisionError, match="inconsistent"):
            db.persist(request)
    finally:
        db.close()


def test_signal_replay_rejects_inconsistent_event_id(tmp_path):
    db = SQLiteDecisionPersistence(tmp_path / "signals.db")
    try:
        request = _signal_request("key-replay-event", "event-replay-event")
        db.persist(request)
        db._connection.execute("UPDATE outbox SET event_id = ? WHERE idempotency_key = ?", ("event-other", request.idempotency_key))
        db._connection.commit()
        with pytest.raises(PersistenceCollisionError, match="inconsistent"):
            db.persist(request)
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


class _PersistInterleavingConnection:
    def __init__(self, connection, interleave):
        self._connection = connection
        self._interleave = interleave
        self._triggered = False

    def execute(self, sql, parameters=()):
        cursor = self._connection.execute(sql, parameters)
        if (
            not self._triggered
            and sql.lstrip().startswith("SELECT payload_json FROM decisions")
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


def test_concurrent_signal_replay_rejects_missing_outbox_after_winner_commits(tmp_path) -> None:
    db = SQLiteDecisionPersistence(tmp_path / "signals.db")
    try:
        request = _signal_request("key-concurrent-replay", "event-concurrent-replay")
        payload = __import__(
            "tabdeal_signal.persistence.sqlite",
            fromlist=["_json_payload"],
        )._json_payload(request)
        raw = db._connection

        def commit_winner_without_outbox():
            raw.execute(
                "INSERT INTO decisions (idempotency_key, decision_status, payload_json, created_at) VALUES (?, ?, ?, ?)",
                (
                    request.idempotency_key,
                    request.decision.status.value,
                    payload,
                    "2026-01-01T00:00:00+00:00",
                ),
            )
            raw.commit()

        db._connection = _PersistInterleavingConnection(
            raw,
            commit_winner_without_outbox,
        )
        with pytest.raises(PersistenceCollisionError, match="missing outbox"):
            db.persist(request)
    finally:
        db.close()
