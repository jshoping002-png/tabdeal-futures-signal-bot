from __future__ import annotations

import json

import pytest

from tabdeal_signal.notifications.worker import NotificationWorker


class FakePersistence:
    def __init__(self, records):
        self.records = records
        self.sent = []
        self.retried = []
        self.dead_lettered = []
        self.quarantined = []

    def claim_pending_outbox(self, now=None, lease_seconds=60, limit=10):
        return list(self.records)[:limit]

    def mark_outbox_sent(self, event_id, sent_at=None, *, owner_id, lease_token):
        self.sent.append((event_id, sent_at, owner_id, lease_token))

    def mark_outbox_retry(self, event_id, next_attempt_at, error, *, owner_id, lease_token):
        self.retried.append((event_id, next_attempt_at, error, owner_id, lease_token))

    def mark_outbox_dead_letter(self, event_id, error, *, owner_id, lease_token):
        self.dead_lettered.append((event_id, error, owner_id, lease_token))

    def quarantine_outbox_record(self, internal_id, error, *, owner_id, lease_token):
        self.quarantined.append((internal_id, error, owner_id, lease_token))


class FakeTransport:
    def __init__(self, error=None):
        self.error = error
        self.calls = []

    def send(self, *, event_id, payload):
        self.calls.append((event_id, payload))
        if self.error is not None:
            raise self.error


def _record(attempt_count=1):
    return {
        "event_id": "event-1",
        "attempt_count": attempt_count,
        "payload_json": '{"decision":"LONG","status":"SIGNAL"}',
        "owner_id": "worker-1",
        "lease_token": "lease-1",
    }


def test_invalid_payload_is_retried_without_transport_call():
    record = _record()
    record["event_id"] = "evt-1"
    record["payload_json"] = "not-json"
    persistence = FakePersistence([record])
    transport = FakeTransport()
    assert NotificationWorker(persistence, transport).run_once(now="2026-01-01T00:00:00+00:00") == 1
    assert transport.calls == []
    assert persistence.retried[0][0] == "evt-1"
    assert persistence.retried[0][1] == "2026-01-01T00:00:30+00:00"
    assert persistence.retried[0][2].startswith("JSONDecodeError:")
    assert persistence.dead_lettered == []


def test_non_object_payload_is_retried_without_transport_call():
    record = _record()
    record["event_id"] = "evt-2"
    record["payload_json"] = json.dumps(["signal"])
    persistence = FakePersistence([record])
    transport = FakeTransport()
    NotificationWorker(persistence, transport).run_once(now="2026-01-01T00:00:00+00:00")
    assert transport.calls == []
    assert len(persistence.retried) == 1


def test_max_attempts_moves_transport_failure_to_dead_letter():
    persistence = FakePersistence([_record(attempt_count=3)])
    transport = FakeTransport(RuntimeError("temporary failure"))
    NotificationWorker(persistence, transport, max_attempts=3).run_once(now="2026-01-01T00:00:00+00:00")
    assert len(transport.calls) == 1
    assert persistence.retried == []
    assert persistence.dead_lettered == [("event-1", "RuntimeError: temporary failure", "worker-1", "lease-1")]


def test_empty_event_id_is_quarantined_without_transport_call():
    record = _record()
    record["internal_id"] = 11
    record["event_id"] = "   "
    persistence = FakePersistence([record])
    NotificationWorker(persistence, FakeTransport()).run_once(now="2026-01-01T00:00:00+00:00")
    assert persistence.quarantined == [
        (11, "invalid event_id: empty or whitespace-only", "worker-1", "lease-1")
    ]
    assert persistence.dead_lettered == []


def test_missing_event_id_is_quarantined_without_transport_call():
    record = _record()
    record["internal_id"] = 12
    del record["event_id"]
    persistence = FakePersistence([record])
    NotificationWorker(persistence, FakeTransport()).run_once(now="2026-01-01T00:00:00+00:00")
    assert persistence.quarantined == [
        (12, "invalid event_id: missing or non-string", "worker-1", "lease-1")
    ]
    assert persistence.dead_lettered == []


def test_non_string_event_id_is_quarantined_without_transport_call():
    record = _record()
    record["internal_id"] = 13
    record["event_id"] = 123
    persistence = FakePersistence([record])
    NotificationWorker(persistence, FakeTransport()).run_once(now="2026-01-01T00:00:00+00:00")
    assert persistence.quarantined == [
        (13, "invalid event_id: missing or non-string", "worker-1", "lease-1")
    ]
    assert persistence.dead_lettered == []


def test_missing_internal_id_does_not_block_delivery():
    record = _record()
    persistence = FakePersistence([record])
    transport = FakeTransport()
    NotificationWorker(persistence, transport).run_once(now="2026-01-01T00:00:00+00:00")
    assert transport.calls == [("event-1", {"decision": "LONG", "status": "SIGNAL"})]
    assert persistence.sent == [
        ("event-1", "2026-01-01T00:00:00+00:00", "worker-1", "lease-1")
    ]
    assert persistence.quarantined == []
    assert persistence.retried == []
    assert persistence.dead_lettered == []


def test_worker_configuration_rejects_invalid_values():
    persistence = FakePersistence([])
    transport = FakeTransport()
    with pytest.raises(ValueError):
        NotificationWorker(persistence, transport, max_attempts=0)
    with pytest.raises(ValueError):
        NotificationWorker(persistence, transport, base_backoff_seconds=0)
    with pytest.raises(ValueError):
        NotificationWorker(persistence, transport, lease_seconds=0)
    with pytest.raises(ValueError):
        NotificationWorker(persistence, transport, batch_size=0)
