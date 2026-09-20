"""SQLite persistence adapter for decisions and signal outbox records.

This adapter is intentionally limited to signal persistence and notification
outbox creation. It does not submit orders or perform any trading action.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import asdict, is_dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from tabdeal_signal.persistence.contracts import PersistenceRequest, PersistenceResult


class PersistenceCollisionError(RuntimeError):
    """Raised when an idempotency key or event id is reused incorrectly."""


class SQLiteDecisionPersistence:
    """Persist decisions and signal outbox entries atomically in SQLite."""

    def __init__(self, database: str | Path) -> None:
        self._database = str(database)
        self._connection = sqlite3.connect(self._database)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA busy_timeout = 5000")
        self._create_schema()

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "SQLiteDecisionPersistence":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

    def _create_schema(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS decisions (
                idempotency_key TEXT PRIMARY KEY,
                decision_status TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS outbox (
                event_id TEXT PRIMARY KEY,
                idempotency_key TEXT NOT NULL UNIQUE,
                payload_json TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PENDING',
                attempt_count INTEGER NOT NULL DEFAULT 0,
                next_attempt_at TEXT,
                locked_until TEXT,
                last_error TEXT,
                sent_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                owner_id TEXT,
                lease_token TEXT,
                FOREIGN KEY (idempotency_key)
                    REFERENCES decisions(idempotency_key)
                    ON DELETE RESTRICT
            );
            """
        )
        self._connection.commit()
        self._ensure_outbox_columns()
        self._validate_schema_state()

    def _validate_schema_state(self) -> None:
        required = {
            "decisions": {"idempotency_key", "decision_status", "payload_json", "created_at"},
            "outbox": {
                "event_id", "idempotency_key", "payload_json", "status",
                "attempt_count", "next_attempt_at", "locked_until", "last_error",
                "sent_at", "created_at", "updated_at", "owner_id", "lease_token",
            },
        }
        for table, columns in required.items():
            actual = {row["name"] for row in self._connection.execute(f"PRAGMA table_info({table})").fetchall()}
            missing = sorted(columns - actual)
            if missing:
                raise RuntimeError(
                    f"persistence schema is incomplete for {table}: missing {', '.join(missing)}"
                )

        invalid_status = self._connection.execute(
            "SELECT event_id, status FROM outbox "
            "WHERE status NOT IN ('PENDING', 'PROCESSING', 'RETRY', 'SENT', 'DEAD_LETTER') LIMIT 1"
        ).fetchone()
        if invalid_status is not None:
            raise RuntimeError(
                f"persistence schema contains invalid outbox status: {invalid_status['status']}"
            )

        invalid_attempt = self._connection.execute(
            "SELECT event_id, attempt_count FROM outbox "
            "WHERE typeof(attempt_count) != 'integer' OR attempt_count < 0 LIMIT 1"
        ).fetchone()
        if invalid_attempt is not None:
            raise RuntimeError(
                f"persistence schema contains invalid outbox attempt_count: {invalid_attempt['attempt_count']}"
            )

        invalid_decision = self._connection.execute(
            "SELECT idempotency_key, decision_status FROM decisions "
            "WHERE typeof(idempotency_key) != 'text' OR trim(idempotency_key) = '' "
            "OR decision_status NOT IN ('SIGNAL', 'BLOCKED') LIMIT 1"
        ).fetchone()
        if invalid_decision is not None:
            raise RuntimeError(
                f"persistence schema contains invalid decision row: {invalid_decision['idempotency_key']}"
            )

        invalid_decision_payload = self._connection.execute(
            "SELECT idempotency_key FROM decisions "
            "WHERE typeof(payload_json) != 'text' OR trim(payload_json) = '' "
            "OR json_valid(payload_json) != 1 LIMIT 1"
        ).fetchone()
        if invalid_decision_payload is not None:
            raise RuntimeError(
                f"persistence schema contains invalid decision payload: {invalid_decision_payload['idempotency_key']}"
            )

        non_object_decision_payload = self._connection.execute(
            "SELECT idempotency_key FROM decisions "
            "WHERE json_valid(payload_json) = 1 AND json_type(payload_json) != 'object' LIMIT 1"
        ).fetchone()
        if non_object_decision_payload is not None:
            raise RuntimeError(
                f"persistence schema contains non-object decision payload: {non_object_decision_payload['idempotency_key']}"
            )

        invalid_outbox = self._connection.execute(
            "SELECT event_id, idempotency_key FROM outbox "
            "WHERE typeof(event_id) != 'text' OR trim(event_id) = '' "
            "OR typeof(idempotency_key) != 'text' OR trim(idempotency_key) = '' LIMIT 1"
        ).fetchone()
        if invalid_outbox is not None:
            raise RuntimeError(
                f"persistence schema contains invalid outbox identity: {invalid_outbox['event_id']}"
            )

        invalid_outbox_payload = self._connection.execute(
            "SELECT event_id FROM outbox "
            "WHERE typeof(payload_json) != 'text' OR trim(payload_json) = '' "
            "OR json_valid(payload_json) != 1 LIMIT 1"
        ).fetchone()
        if invalid_outbox_payload is not None:
            raise RuntimeError(
                f"persistence schema contains invalid outbox payload: {invalid_outbox_payload['event_id']}"
            )

        non_object_outbox_payload = self._connection.execute(
            "SELECT event_id FROM outbox "
            "WHERE json_valid(payload_json) = 1 AND json_type(payload_json) != 'object' LIMIT 1"
        ).fetchone()
        if non_object_outbox_payload is not None:
            raise RuntimeError(
                f"persistence schema contains non-object outbox payload: {non_object_outbox_payload['event_id']}"
            )

        invalid_sent_state = self._connection.execute(
            "SELECT event_id FROM outbox "
            "WHERE (status = 'SENT' AND sent_at IS NULL) "
            "OR (status != 'SENT' AND sent_at IS NOT NULL) LIMIT 1"
        ).fetchone()
        if invalid_sent_state is not None:
            raise RuntimeError(
                f"persistence schema contains invalid sent_at state: {invalid_sent_state['event_id']}"
            )

        invalid_dead_letter = self._connection.execute(
            "SELECT event_id FROM outbox "
            "WHERE status = 'DEAD_LETTER' AND (last_error IS NULL OR trim(last_error) = '') LIMIT 1"
        ).fetchone()
        if invalid_dead_letter is not None:
            raise RuntimeError(
                f"persistence schema contains invalid dead-letter state: {invalid_dead_letter['event_id']}"
            )

        invalid_link = self._connection.execute(
            "SELECT o.event_id FROM outbox o "
            "LEFT JOIN decisions d ON d.idempotency_key = o.idempotency_key "
            "WHERE d.idempotency_key IS NULL LIMIT 1"
        ).fetchone()
        if invalid_link is not None:
            raise RuntimeError(
                f"persistence schema contains orphan outbox record: {invalid_link['event_id']}"
            )

        decision_pk = self._connection.execute(
            "SELECT pk FROM pragma_table_info('decisions') "
            "WHERE name = 'idempotency_key'"
        ).fetchone()
        if decision_pk is None or decision_pk["pk"] != 1:
            raise RuntimeError(
                "persistence schema requires decisions.idempotency_key to be the primary key"
            )

        outbox_pk = self._connection.execute(
            "SELECT pk FROM pragma_table_info('outbox') "
            "WHERE name = 'event_id'"
        ).fetchone()
        if outbox_pk is None or outbox_pk["pk"] != 1:
            raise RuntimeError(
                "persistence schema requires outbox.event_id to be the primary key"
            )

        unique_indexes = self._connection.execute(
            "SELECT name FROM pragma_index_list('outbox') WHERE \"unique\" = 1"
        ).fetchall()
        if not any(
            self._connection.execute(
                "SELECT 1 FROM pragma_index_info(?) WHERE name = 'idempotency_key'",
                (row["name"],),
            ).fetchone()
            for row in unique_indexes
        ):
            raise RuntimeError(
                "persistence schema requires outbox.idempotency_key to be UNIQUE"
            )

        inconsistent_lease = self._connection.execute(
            "SELECT event_id FROM outbox "
            "WHERE status = 'PROCESSING' "
            "AND (owner_id IS NULL OR lease_token IS NULL OR locked_until IS NULL) LIMIT 1"
        ).fetchone()
        if inconsistent_lease is not None:
            raise RuntimeError(
                f"persistence schema contains incomplete outbox lease ownership: {inconsistent_lease['event_id']}"
            )

        stale_lease_fields = self._connection.execute(
            "SELECT event_id FROM outbox "
            "WHERE status != 'PROCESSING' "
            "AND (owner_id IS NOT NULL OR lease_token IS NOT NULL OR locked_until IS NOT NULL) LIMIT 1"
        ).fetchone()
        if stale_lease_fields is not None:
            raise RuntimeError(
                f"persistence schema contains lease fields outside PROCESSING: {stale_lease_fields['event_id']}"
            )

        for row in self._connection.execute(
            "SELECT event_id, created_at, updated_at, next_attempt_at, locked_until, sent_at "
            "FROM outbox"
        ).fetchall():
            for field in ("created_at", "updated_at", "next_attempt_at", "locked_until", "sent_at"):
                value = row[field]
                if value is not None:
                    _validate_persisted_timestamp(
                        value, f"outbox {row['event_id']} {field}"
                    )

        for row in self._connection.execute(
            "SELECT idempotency_key, created_at FROM decisions"
        ).fetchall():
            _validate_persisted_timestamp(
                row["created_at"], f"decision {row['idempotency_key']} created_at"
            )

    def _ensure_outbox_columns(self) -> None:
        """Add lifecycle columns to databases created by earlier revisions."""
        existing = {
            row["name"]
            for row in self._connection.execute("PRAGMA table_info(outbox)").fetchall()
        }
        additions = {
            "attempt_count": "INTEGER NOT NULL DEFAULT 0",
            "next_attempt_at": "TEXT",
            "locked_until": "TEXT",
            "last_error": "TEXT",
            "sent_at": "TEXT",
            "updated_at": "TEXT",
            "owner_id": "TEXT",
            "lease_token": "TEXT",
        }
        for name, definition in additions.items():
            if name not in existing:
                if name == "updated_at":
                    self._connection.execute("ALTER TABLE outbox ADD COLUMN updated_at TEXT")
                    self._connection.execute(
                        "UPDATE outbox SET updated_at = created_at WHERE updated_at IS NULL"
                    )
                else:
                    self._connection.execute(
                        f"ALTER TABLE outbox ADD COLUMN {name} {definition}"
                    )
        self._connection.commit()

    def persist(self, request: PersistenceRequest) -> PersistenceResult:
        payload = _json_payload(request)
        key = request.idempotency_key
        existing = self._connection.execute(
            "SELECT payload_json FROM decisions WHERE idempotency_key = ?", (key,)
        ).fetchone()
        if existing is not None:
            if existing["payload_json"] != payload:
                raise PersistenceCollisionError(f"idempotency key collision: {key}")
            status = getattr(getattr(request.decision, "status", None), "value", request.decision.status)
            persisted_status = self._connection.execute(
                "SELECT decision_status FROM decisions WHERE idempotency_key = ?",
                (key,),
            ).fetchone()
            if persisted_status is None or persisted_status["decision_status"] != status:
                raise PersistenceCollisionError(
                    f"decision persistence is inconsistent: {key}"
                )
            if status == "SIGNAL":
                event_id = _event_id(request)
                outbox = self._connection.execute(
                    "SELECT event_id, idempotency_key, payload_json FROM outbox WHERE idempotency_key = ?",
                    (key,),
                ).fetchone()
                if outbox is None:
                    raise PersistenceCollisionError(f"signal persistence is incomplete: missing outbox for {key}")
                if outbox["event_id"] != event_id or outbox["payload_json"] != payload:
                    raise PersistenceCollisionError(f"signal persistence is inconsistent: {key}")
            else:
                orphan_outbox = self._connection.execute(
                    "SELECT event_id FROM outbox WHERE idempotency_key = ?",
                    (key,),
                ).fetchone()
                if orphan_outbox is not None:
                    raise PersistenceCollisionError(
                        f"non-signal persistence is inconsistent: {key}"
                    )
            return PersistenceResult(persisted=True, idempotent_replay=True)

        decision = request.decision
        status = getattr(getattr(decision, "status", None), "value", decision.status)
        created_at = _utc_now()
        event_id = _event_id(request)

        try:
            with self._connection:
                self._connection.execute(
                    "INSERT INTO decisions "
                    "(idempotency_key, decision_status, payload_json, created_at) "
                    "VALUES (?, ?, ?, ?)",
                    (key, status, payload, created_at),
                )
                if status == "SIGNAL":
                    self._connection.execute(
                        "INSERT INTO outbox "
                        "(event_id, idempotency_key, payload_json, created_at, updated_at) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (event_id, key, payload, created_at, created_at),
                    )
        except sqlite3.IntegrityError as exc:
            # Another writer may have committed the same idempotency key after
            # the preflight read. Treat an identical payload as a replay; only
            # a different payload is a collision. Other integrity failures
            # (for example an event_id collision) remain explicit failures.
            concurrent = self._connection.execute(
                "SELECT payload_json, decision_status FROM decisions WHERE idempotency_key = ?",
                (key,),
            ).fetchone()
            if concurrent is not None:
                if concurrent["payload_json"] != payload:
                    raise PersistenceCollisionError(
                        f"idempotency key collision: {key}"
                    ) from exc
                if concurrent["decision_status"] != status:
                    raise PersistenceCollisionError(
                        f"decision persistence is inconsistent: {key}"
                    ) from exc
                if status == "SIGNAL":
                    event_id = _event_id(request)
                    outbox = self._connection.execute(
                        "SELECT event_id, payload_json FROM outbox WHERE idempotency_key = ?",
                        (key,),
                    ).fetchone()
                    if outbox is None:
                        raise PersistenceCollisionError(
                            f"signal persistence is incomplete: missing outbox for {key}"
                        ) from exc
                    if (
                        outbox["event_id"] != event_id
                        or outbox["payload_json"] != payload
                    ):
                        raise PersistenceCollisionError(
                            f"signal persistence is inconsistent: {key}"
                        ) from exc
                else:
                    orphan_outbox = self._connection.execute(
                        "SELECT event_id FROM outbox WHERE idempotency_key = ?",
                        (key,),
                    ).fetchone()
                    if orphan_outbox is not None:
                        raise PersistenceCollisionError(
                            f"non-signal persistence is inconsistent: {key}"
                        ) from exc
                return PersistenceResult(persisted=True, idempotent_replay=True)
            raise PersistenceCollisionError(str(exc)) from exc

        return PersistenceResult(persisted=True, idempotent_replay=False)

    def claim_pending_outbox(
        self,
        now: str | None = None,
        lease_seconds: int = 60,
        limit: int = 10,
        owner_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Atomically claim eligible records and assign an ownership token."""
        if (isinstance(lease_seconds, bool) or not isinstance(lease_seconds, int) or lease_seconds <= 0 or isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0):
            raise ValueError("lease_seconds and limit must be positive integers")
        if owner_id is not None and (
            not isinstance(owner_id, str) or not owner_id.strip()
        ):
            raise ValueError("owner_id must be a non-empty string when provided")
        current = _utc_timestamp(now)
        owner = owner_id if owner_id is not None else f"worker:{uuid.uuid4()}"
        locked_until = _plus_seconds(current, lease_seconds)
        claimed: list[dict[str, Any]] = []
        with self._connection:
            rows = self._connection.execute(
                """
                SELECT rowid AS internal_id FROM outbox
                WHERE (
                    status = 'PENDING'
                    OR (status = 'RETRY' AND (next_attempt_at IS NULL OR next_attempt_at <= ?))
                    OR (status = 'PROCESSING' AND locked_until IS NOT NULL AND locked_until <= ?)
                )
                ORDER BY created_at, event_id LIMIT ?
                """,
                (current, current, limit),
            ).fetchall()
            for row in rows:
                token = str(uuid.uuid4())
                self._connection.execute(
                    """
                    UPDATE outbox
                    SET status = 'PROCESSING', attempt_count = attempt_count + 1,
                        locked_until = ?, updated_at = ?, last_error = NULL,
                        owner_id = ?, lease_token = ?
                    WHERE rowid = ?
                      AND (
                          status = 'PENDING'
                          OR (status = 'RETRY' AND (next_attempt_at IS NULL OR next_attempt_at <= ?))
                          OR (status = 'PROCESSING' AND locked_until IS NOT NULL AND locked_until <= ?)
                      )
                    """,
                    (locked_until, current, owner, token, row["internal_id"], current, current),
                )
                if self._connection.execute("SELECT changes()").fetchone()[0] != 1:
                    continue
                item = self._connection.execute(
                    "SELECT rowid AS internal_id, * FROM outbox WHERE rowid = ?",
                    (row["internal_id"],),
                ).fetchone()
                if item is not None:
                    claimed.append(dict(item))
        return claimed

    @staticmethod
    def _validate_event_id(event_id: str) -> None:
        if not isinstance(event_id, str) or not event_id.strip():
            raise ValueError("event_id must be a non-empty string")

    @staticmethod
    def _validate_lease(owner_id: str, lease_token: str) -> None:
        if (
            not isinstance(owner_id, str)
            or not owner_id.strip()
            or not isinstance(lease_token, str)
            or not lease_token.strip()
        ):
            raise ValueError("owner_id and lease_token must be non-empty strings")

    def mark_outbox_sent(
        self,
        event_id: str,
        sent_at: str | None = None,
        *,
        owner_id: str,
        lease_token: str,
    ) -> None:
        self._validate_event_id(event_id)
        self._validate_lease(owner_id, lease_token)
        timestamp = _utc_timestamp(sent_at)
        checked_at = _utc_now()
        with self._connection:
            cursor = self._connection.execute(
                """
                UPDATE outbox
                SET status='SENT', sent_at=?, locked_until=NULL,
                    next_attempt_at=NULL, last_error=NULL, updated_at=?,
                    owner_id=NULL, lease_token=NULL
                WHERE event_id = ? AND status = 'PROCESSING'
                  AND owner_id = ? AND lease_token = ?
                  AND locked_until IS NOT NULL AND locked_until > ?
                """,
                (timestamp, checked_at, event_id, owner_id, lease_token, checked_at),
            )
            if cursor.rowcount != 1:
                raise ValueError(f"outbox event lease is invalid: {event_id}")

    def mark_outbox_retry(
        self,
        event_id: str,
        next_attempt_at: str,
        error: str,
        *,
        owner_id: str,
        lease_token: str,
    ) -> None:
        if not isinstance(error, str) or not error.strip():
            raise ValueError("error must be a non-empty string")
        self._validate_event_id(event_id)
        self._validate_lease(owner_id, lease_token)
        timestamp = _utc_now()
        retry_at = _utc_timestamp(next_attempt_at)
        with self._connection:
            cursor = self._connection.execute(
                """
                UPDATE outbox
                SET status='RETRY', next_attempt_at=?, locked_until=NULL,
                    last_error=?, updated_at=?, owner_id=NULL, lease_token=NULL
                WHERE event_id = ? AND status = 'PROCESSING'
                  AND owner_id = ? AND lease_token = ?
                  AND locked_until IS NOT NULL AND locked_until > ?
                """,
                (
                    retry_at,
                    error,
                    timestamp,
                    event_id,
                    owner_id,
                    lease_token,
                    timestamp,
                ),
            )
            if cursor.rowcount != 1:
                raise ValueError(f"outbox event lease is invalid: {event_id}")

    def mark_outbox_dead_letter(
        self,
        event_id: str,
        error: str,
        *,
        owner_id: str,
        lease_token: str,
    ) -> None:
        if not isinstance(error, str) or not error.strip():
            raise ValueError("error must be a non-empty string")
        self._validate_event_id(event_id)
        self._validate_lease(owner_id, lease_token)
        timestamp = _utc_now()
        with self._connection:
            cursor = self._connection.execute(
                """
                UPDATE outbox
                SET status='DEAD_LETTER', locked_until=NULL,
                    last_error=?, updated_at=?, owner_id=NULL, lease_token=NULL
                WHERE event_id = ? AND status = 'PROCESSING'
                  AND owner_id = ? AND lease_token = ?
                  AND locked_until IS NOT NULL AND locked_until > ?
                """,
                (error, timestamp, event_id, owner_id, lease_token, timestamp),
            )
            if cursor.rowcount != 1:
                raise ValueError(f"outbox event lease is invalid: {event_id}")

    def quarantine_outbox_record(
        self,
        internal_id: int,
        error: str,
        *,
        owner_id: str,
        lease_token: str,
    ) -> None:
        if isinstance(internal_id, bool) or not isinstance(internal_id, int) or internal_id <= 0:
            raise ValueError("internal_id must be a positive integer")
        if not isinstance(error, str) or not error.strip():
            raise ValueError("error must be a non-empty string")
        self._validate_lease(owner_id, lease_token)
        timestamp = _utc_now()
        with self._connection:
            cursor = self._connection.execute(
                """
                UPDATE outbox
                SET status='DEAD_LETTER', locked_until=NULL,
                    last_error=?, updated_at=?, owner_id=NULL, lease_token=NULL
                WHERE rowid = ? AND status = 'PROCESSING'
                  AND owner_id = ? AND lease_token = ?
                  AND locked_until IS NOT NULL AND locked_until > ?
                """,
                (error, timestamp, internal_id, owner_id, lease_token, timestamp),
            )
            if cursor.rowcount != 1:
                raise ValueError(f"outbox row lease is invalid: {internal_id}")

    def recover_expired_processing(self, now: str | None = None) -> int:
        """Return expired leases to RETRY without creating new events."""
        current = _utc_timestamp(now)
        with self._connection:
            cursor = self._connection.execute(
                """
                UPDATE outbox
                SET status = 'RETRY', locked_until = NULL, owner_id = NULL, lease_token = NULL,
                    next_attempt_at = ?, last_error = COALESCE(last_error, 'lease expired'),
                    updated_at = ?
                WHERE status = 'PROCESSING' AND locked_until IS NOT NULL
                  AND locked_until <= ?
                """,
                (current, current, current),
            )
            return cursor.rowcount


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _utc_timestamp(value: str | None) -> str:
    timestamp = _utc_now() if value is None else value
    if not isinstance(timestamp, str) or not timestamp.strip():
        raise ValueError("timestamp must be a non-empty ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(timestamp)
    except ValueError as exc:
        raise ValueError("timestamp must be a valid ISO-8601 string") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return parsed.astimezone(timezone.utc).isoformat()


def _validate_persisted_timestamp(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"persistence contains invalid {field} timestamp")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise RuntimeError(f"persistence contains invalid {field} timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise RuntimeError(f"persistence contains timezone-naive {field} timestamp")
    if parsed.astimezone(timezone.utc).isoformat() != value:
        raise RuntimeError(f"persistence contains non-canonical UTC {field} timestamp")


def _plus_seconds(timestamp: str, seconds: int) -> str:
    value = datetime.fromisoformat(timestamp)
    return (value + timedelta(seconds=seconds)).astimezone(timezone.utc).isoformat()


def _event_id(request: PersistenceRequest) -> str:
    explicit = getattr(request, "event_id", None)
    if explicit:
        return str(explicit)
    return f"signal:{request.idempotency_key}"


def _json_payload(value: Any) -> str:
    def encode(item: Any) -> Any:
        if isinstance(item, Enum):
            return item.value
        if isinstance(item, datetime):
            return item.isoformat()
        if is_dataclass(item):
            return {key: encode(val) for key, val in asdict(item).items()}
        if isinstance(item, dict):
            return {str(key): encode(val) for key, val in item.items()}
        if isinstance(item, (list, tuple)):
            return [encode(val) for val in item]
        return item

    return json.dumps(encode(value), sort_keys=True, separators=(",", ":"))