"""Signal outbox worker.

This worker delivers persisted signal notifications only. It must never
submit orders, execute trades, or call an exchange trading endpoint.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol

from tabdeal_signal.notifications.transport import NotificationTransport


class OutboxPersistence(Protocol):
    """Minimal persistence surface required by the notification worker."""

    def claim_pending_outbox(self, now: str | None = None, lease_seconds: int = 60, limit: int = 10) -> list[dict[str, Any]]: ...
    def mark_outbox_sent(self, event_id: str, sent_at: str | None = None, owner_id: str | None = None, lease_token: str | None = None) -> None: ...
    def mark_outbox_retry(self, event_id: str, next_attempt_at: str, error: str, owner_id: str | None = None, lease_token: str | None = None) -> None: ...
    def mark_outbox_dead_letter(self, event_id: str, error: str, owner_id: str | None = None, lease_token: str | None = None) -> None: ...
    def quarantine_outbox_record(self, internal_id: int, error: str, owner_id: str | None = None, lease_token: str | None = None) -> None: ...


class NotificationWorker:
    """Deliver claimed signal outbox records with bounded retry behavior."""

    def __init__(self, persistence: OutboxPersistence, transport: NotificationTransport, *, max_attempts: int = 3, base_backoff_seconds: int = 30, lease_seconds: int = 60, batch_size: int = 10) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be positive")
        if base_backoff_seconds < 1:
            raise ValueError("base_backoff_seconds must be positive")
        if lease_seconds < 1 or batch_size < 1:
            raise ValueError("lease_seconds and batch_size must be positive")
        self._persistence = persistence
        self._transport = transport
        self._max_attempts = max_attempts
        self._base_backoff_seconds = base_backoff_seconds
        self._lease_seconds = lease_seconds
        self._batch_size = batch_size
        self._owner_id = f"worker:{uuid.uuid4()}"

    def run_once(self, *, now: str | None = None) -> int:
        current = now or _utc_now()
        try:
            records = self._persistence.claim_pending_outbox(now=current, lease_seconds=self._lease_seconds, limit=self._batch_size, owner_id=self._owner_id)
        except TypeError:
            records = self._persistence.claim_pending_outbox(now=current, lease_seconds=self._lease_seconds, limit=self._batch_size)
        for record in records:
            self._process_record(record, current=current)
        return len(records)

    def _process_record(self, record: Mapping[str, Any], *, current: str) -> None:
        event_id = record.get("event_id")
        if not isinstance(event_id, str) or not event_id.strip():
            internal_id = record.get("internal_id")
            if isinstance(internal_id, int) and internal_id > 0:
                reason = "invalid event_id: missing or non-string"
                if isinstance(event_id, str):
                    reason = "invalid event_id: empty or whitespace-only"
                self._persistence.quarantine_outbox_record(internal_id, reason)
            return

        owner_id = record.get("owner_id")
        lease_token = record.get("lease_token")

        try:
            payload = json.loads(record["payload_json"])
            if not isinstance(payload, Mapping):
                raise ValueError("outbox payload must decode to an object")
            self._transport.send(event_id=event_id, payload=payload)
        except Exception as exc:
            error = _error_text(exc)
            attempts = int(record.get("attempt_count") or 0)
            if attempts >= self._max_attempts:
                self._finalize("mark_outbox_dead_letter", event_id, error, owner_id, lease_token)
            else:
                delay = self._base_backoff_seconds * (2 ** max(attempts - 1, 0))
                self._finalize("mark_outbox_retry", event_id, _plus_seconds(current, delay), error, owner_id, lease_token)
            return

        self._finalize("mark_outbox_sent", event_id, current, owner_id, lease_token)

    def _finalize(self, method: str, event_id: str, *args: Any) -> None:
        fn = getattr(self._persistence, method)
        if len(args) >= 2 and args[-2] is not None and args[-1] is not None:
            try:
                fn(event_id, *args[:-2], owner_id=args[-2], lease_token=args[-1])
                return
            except TypeError:
                pass
        fn(event_id, *args[:-2] if len(args) >= 2 else args)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _plus_seconds(timestamp: str, seconds: int) -> str:
    return (datetime.fromisoformat(timestamp) + timedelta(seconds=seconds)).isoformat()


def _error_text(error: Exception) -> str:
    text = str(error).strip()
    return f"{type(error).__name__}: {text}" if text else type(error).__name__
