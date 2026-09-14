from __future__ import annotations

from dataclasses import dataclass

from tabdeal_signal.notifications.worker import NotificationWorker


@dataclass
class FakePersistence:
    records: list[dict]

    def __post_init__(self) -> None:
        self.sent: list[str] = []
        self.retried: list[tuple[str, str, str]] = []
        self.dead: list[tuple[str, str]] = []
        self.quarantined: list[tuple[int, str]] = []

    def claim_pending_outbox(self, now=None, lease_seconds=60, limit=10):
        return self.records

    def mark_outbox_sent(self, event_id, sent_at=None):
        self.sent.append(event_id)

    def mark_outbox_retry(self, event_id, next_attempt_at, error):
        self.retried.append((event_id, next_attempt_at, error))

    def mark_outbox_dead_letter(self, event_id, error):
        self.dead.append((event_id, error))

    def quarantine_outbox_record(self, internal_id, error):
        self.quarantined.append((internal_id, error))


class FakeTransport:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.calls: list[tuple[str, dict]] = []

    def send(self, *, event_id, payload):
        self.calls.append((event_id, dict(payload)))
        if self.error is not None:
            raise self.error


def _record(attempt_count=1):
    return {
        "event_id": "event-1",
        "attempt_count": attempt_count,
        "payload_json": '{"decision":"LONG","status":"SIGNAL"}',
    }


def test_successful_delivery_marks_sent():
    persistence = FakePersistence([_record()])
    transport = FakeTransport()

    count = NotificationWorker(persistence, transport).run_once(
        now="2026-01-01T00:00:00+00:00"
    )

    assert count == 1
    assert transport.calls == [("event-1", {"decision": "LONG", "status": "SIGNAL"})]
    assert persistence.sent == ["event-1"]
    assert persistence.retried == []
    assert persistence.dead == []


def test_transient_failure_schedules_retry():
    persistence = FakePersistence([_record(attempt_count=1)])
    transport = FakeTransport(RuntimeError("temporary"))

    NotificationWorker(
        persistence, transport, base_backoff_seconds=30
    ).run_once(now="2026-01-01T00:00:00+00:00")

    assert persistence.sent == []
    assert persistence.dead == []
    assert persistence.retried == [
        ("event-1", "2026-01-01T00:00:30+00:00", "RuntimeError: temporary")
    ]


def test_max_attempts_moves_record_to_dead_letter():
    persistence = FakePersistence([_record(attempt_count=3)])
    transport = FakeTransport(RuntimeError("permanent"))

    NotificationWorker(persistence, transport, max_attempts=3).run_once(
        now="2026-01-01T00:00:00+00:00"
    )

    assert persistence.sent == []
    assert persistence.retried == []
    assert persistence.dead == [("event-1", "RuntimeError: permanent")]
