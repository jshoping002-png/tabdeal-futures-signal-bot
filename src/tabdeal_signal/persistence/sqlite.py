"""SQLite persistence adapter for decisions and signal outbox records.

This adapter is intentionally limited to signal persistence and notification
outbox creation. It does not submit orders or perform any trading action.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, is_dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from tabdeal_signal.persistence.contracts import PersistenceRequest, PersistenceResult


class PersistenceCollisionError(RuntimeError):
    """Raised when an idempotency key is reused with different content."""


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
                created_at TEXT NOT NULL,
                FOREIGN KEY (idempotency_key)
                    REFERENCES decisions(idempotency_key)
                    ON DELETE RESTRICT
            );
            """
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
                raise PersistenceCollisionError(
                    f"idempotency key collision: {key}"
                )
            return PersistenceResult(persisted=False, idempotent_replay=True)

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
                        "(event_id, idempotency_key, payload_json, created_at) "
                        "VALUES (?, ?, ?, ?)",
                        (event_id, key, payload, created_at),
                    )
        except sqlite3.IntegrityError as exc:
            raise PersistenceCollisionError(str(exc)) from exc

        return PersistenceResult(persisted=True, idempotent_replay=False)


def _utc_now() -> str:
    return datetime.now().astimezone().isoformat()


def _event_id(request: PersistenceRequest) -> str:
    explicit = getattr(request, "event_id", None)
    if explicit:
        return str(explicit)
    # Stable fallback keeps the current contract usable until event_id is
    # promoted to a required field in PersistenceRequest.
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
