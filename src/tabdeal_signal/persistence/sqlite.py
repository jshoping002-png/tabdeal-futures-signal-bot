"""SQLite persistence adapter for decisions and signal outbox records.

This adapter is intentionally limited to signal persistence and notification
outbox creation. It does not submit orders or perform any trading action.
"""

from __future__ import annotations

import json
import sqlite3
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
                FOREIGN KEY (idempotency_key)
                    REFERENCES decisions(idempotency_key)
                    ON DELETE RESTRICT
            );
            """
        )
        self._connection.commit()
        self._ensure_outbox_columns()

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
            raise PersistenceCollisionError(str(exc)) from exc

        return PersistenceResult(persisted=True, idempotent_replay=False)

    def claim_pending_outbox(
        self, now: str | None = None, lease_seconds: int = 60, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Atomically claim eligible records for notification delivery."""
        if lease_seconds <= 0 or limit <= 0:
            raise ValueError("lease_seconds and limit must be positive")
        current = now or _utc_now()
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
                ORDER BY created_at, event_id
                LIMIT ?
                """,
                (current, current, limit),
            ).fetchall()
            for row in rows:
                self._connection.execute(
                    """
                    UPDATE outbox
                    SET status = 'PROCESSING',
                        attempt_count = attempt_count + 1,
                        locked_until = ?,
                        updated_at = ?,
                        last_error = NULL
                    WHERE rowid = ?
                    """,
                   (locked_until, current, row["internal_id"])
                )
                item = self._connection.execute(
                    "SELECT rowid AS internal_id, * FROM outbox WHERE rowid = ?",
                    (row["internal_id"],),
                ).fetchone()
                if item is not None:
                    claimed.append(dict(item))
        return claimed

    def mark_outbox_sent(self, event_id: str, sent_at: str | None = None) -> None:
        timestamp = sent_at or _utc_now()
        with self._connection:
            cursor = self._connection.execute(
                """
                UPDATE outbox
                SET status = 'SENT', sent_at = ?, locked_until = NULL,
                    next_attempt_at = NULL, last_error = NULL, updated_at = ?
                WHERE event_id = ? AND status = 'PROCESSING'
                """,
                (timestamp, timestamp, event_id),
            )
            if cursor.rowcount != 1:
                raise ValueError(f"outbox event is not processing: {event_id}")

    def mark_outbox_retry(self, event_id: str, next_attempt_at: str, error: str) -> None:
        if not error.strip():
            raise ValueError("error must be non-empty")
        with self._connection:
            cursor = self._connection.execute(
                """
                UPDATE outbox
                SET status = 'RETRY', next_attempt_at = ?, locked_until = NULL,
                    last_error = ?, updated_at = ?
                WHERE event_id = ? AND status = 'PROCESSING'
                """,
                (next_attempt_at, error, _utc_now(), event_id),
            )
            if cursor.rowcount != 1:
                raise ValueError(f"outbox event is not processing: {event_id}")

    def mark_outbox_dead_letter(self, event_id: str, error: str) -> None:
        if not error.strip():
            raise ValueError("error must be non-empty")
        with self._connection:
            cursor = self._connection.execute(
                """
                UPDATE outbox
                SET status = 'DEAD_LETTER', locked_until = NULL,
                    last_error = ?, updated_at = ?
                WHERE event_id = ? AND status = 'PROCESSING'
                """,
                (error, _utc_now(), event_id),
            )
            if cursor.rowcount != 1:
                raise ValueError(f"outbox event is not processing: {event_id}")

    def quarantine_outbox_record(self, internal_id: int, error: str) -> None:
        """Dead-letter a malformed claimed row without trusting its event id."""
        if not isinstance(internal_id, int) or internal_id <= 0:
            raise ValueError("internal_id must be positive")
        if not error.strip():
            raise ValueError("error must be non-empty")
        with self._connection:
            cursor = self._connection.execute(
                """
                UPDATE outbox
                SET status = 'DEAD_LETTER', locked_until = NULL,
                    last_error = ?, updated_at = ?
                WHERE rowid = ? AND status = 'PROCESSING'
                """,
                (error, _utc_now(), internal_id),
            )
            if cursor.rowcount != 1:
                raise ValueError(f"outbox row is not processing: {internal_id}")

    def recover_expired_processing(self, now: str | None = None) -> int:
        """Return expired leases to RETRY without creating new events."""
        current = now or _utc_now()
        with self._connection:
            cursor = self._connection.execute(
                """
                UPDATE outbox
                SET status = 'RETRY', locked_until = NULL,
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


def _plus_seconds(timestamp: str, seconds: int) -> str:
    value = datetime.fromisoformat(timestamp)
    return (value + timedelta(seconds=seconds)).isoformat()


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
