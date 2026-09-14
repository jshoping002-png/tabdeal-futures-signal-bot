# Outbox Operations Runbook

This runbook covers the signal-notification outbox only. It does **not** authorize order submission, trading, or any exchange execution.

## Scope

The outbox is responsible for durable delivery attempts of persisted `SIGNAL` notifications. `BLOCKED` decisions do not create notification records.

Supported lifecycle states:

- `PENDING`: persisted and waiting for delivery
- `PROCESSING`: claimed by a worker with a lease
- `RETRY`: eligible for another delivery attempt after `next_attempt_at`
- `SENT`: delivery completed
- `DEAD_LETTER`: delivery is permanently quarantined or exhausted

## Recovery procedure

1. Stop or pause competing notification workers before manual intervention.
2. Open the SQLite database using the same database path configured for the service.
3. Inspect records in `PROCESSING` whose `locked_until` is in the past.
4. Run the adapter's `recover_expired_processing(now=...)` operation.
5. Confirm that recovered rows are now `RETRY`, have `locked_until = NULL`, and have `next_attempt_at` set to the recovery timestamp.
6. Resume one worker and verify that only eligible `PENDING`/`RETRY` rows are claimed.
7. Check that `SENT` rows are not claimed again.

Recovery must not create a new `event_id`, duplicate a decision, or change a decision's business status.

## Malformed records

If a claimed record has a missing, empty, or non-string `event_id`, the worker must not invent a replacement identifier. When an internal row identifier is available, the record is quarantined to `DEAD_LETTER` with a non-empty diagnostic error.

If no stable internal identifier is available, the worker must not acknowledge the record as sent and must not fabricate a retry identity. The persistence API must be extended before such a record can be safely finalized.

## Minimum operational checks

For each worker cycle, operators should be able to determine:

- number of rows claimed;
- number marked `SENT`;
- number moved to `RETRY`;
- number moved to `DEAD_LETTER`;
- number quarantined for malformed identity;
- oldest pending/retry record age;
- number of expired leases recovered;
- transport failure and timeout counts.

These signals are operational requirements. Their production collection and alerting are not implied by this document and remain to be implemented and verified.

## Safety boundary

This component may format and deliver signal notifications. It must never submit orders, invoke trading endpoints, place positions, or perform any exchange execution as part of outbox processing or recovery.
