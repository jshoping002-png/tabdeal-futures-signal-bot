"""Signal outbox worker.

This worker delivers persisted signal notifications only. It must never
submit orders, execute trades, or call an exchange trading endpoint.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol

from tabdeal_signal.notifications.transport import NotificationTransport


class OutboxPersistence(Protocol):
    """Minimal persistence surface required by the notification worker."""

    def claim_pending_outbox(
        self, now: str | None = None, lease_seconds: int = 60, limit: int = 10
    ) -> list[dict[str, Any]]:
        ...

    def mark_outbox_sent(self, event_id: str, sent_at: str | None = None) -> None:
        ...

    def mark_outbox_retry(
        self, event_id: str, next_attempt_at: str, error: str
    ) -> None:
        ...

    def mark_outbox_dead_letter(self, event_id: str, error: str) -> None:
        ...


class NotificationWorker:
    """Deliver claimed signal outbox records with bounded retry behavior."""

    def __init__(
        self,
        persistence: OutboxPersistence,
        transport: NotificationTransport,
        *,
        max_attempts: int = 3,
        base_backoff_seconds: int = 30,
        lease_seconds: int = 60,
        batch_size: int = 10,
    ) -> None:
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

    def run_once(self, *, now: str | None = None) -> int:
        """Claim and process one batch; return the number of claimed records."""
        current = now or _utc_now()
        records = self._persistence.claim_pending_outbox(
            now=current,
            lease_seconds=self._lease_seconds,
            limit=self._batch_size,
        )
        for record in records:
            self._process_record(record, current=current)
        return len(records)

    def _process_record(self, record: Mapping[str, Any], *, current: str) -> None:
        event_id = record.get("event_id")
        if not isinstance(event_id, str) or not event_id.strip():
            if isinstance(event_id, str):
                self._persistence.mark_outbox_dead_letter(
                    event_id, "invalid event_id: empty or whitespace-only"
                )
            return

        try:
            payload = json.loads(record["payload_json"])
            if not isinstance(payload, Mapping):
                raise ValueError("outbox payload must decode to an object")
            self._transport.send(event_id=event_id, payload=payload)
        except Exception as exc:  # transport and payload failures are isolated per event
            error = _error_text(exc)
            attempts = int(record.get("attempt_count") or 0)
            if attempts >= self._max_attempts:
                self._persistence.mark_outbox_dead_letter(event_id, error)
            else:
                delay = self._base_backoff_seconds * (2 ** max(attempts - 1, 0))
                next_attempt = _plus_seconds(current, delay)
                self._persistence.mark_outbox_retry(event_id, next_attempt, error)
            return

        self._persistence.mark_outbox_sent(event_id, sent_at=current)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _plus_seconds(timestamp: str, seconds: int) -> str:
    value = datetime.fromisoformat(timestamp)
    return (value + timedelta(seconds=seconds)).isoformat()


def _error_text(error: Exception) -> str:
    text = str(error).strip()
    return f"{type(error).__name__}: {text}" if text else type(error).__name__
