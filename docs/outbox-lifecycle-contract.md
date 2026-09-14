# Outbox Lifecycle Contract

## Scope

The outbox is used only for delivering already-created signal notifications.
It must never submit orders, place trades, or invoke an exchange execution API.

## States

An outbox record uses one of these states:

- `PENDING`: created atomically with the corresponding `SIGNAL` decision and not yet claimed for delivery.
- `PROCESSING`: temporarily claimed by a delivery worker.
- `SENT`: delivery was acknowledged successfully.
- `RETRY`: delivery failed but may be attempted again according to the retry policy.
- `DEAD_LETTER`: delivery is permanently stopped after the retry limit or an explicit terminal failure.

## Required invariants

1. A `BLOCKED` decision must not create an outbox record.
2. A `SIGNAL` decision and its initial `PENDING` outbox record must be committed in one database transaction.
3. A failed outbox insert must roll back the associated decision insert.
4. `event_id` is globally unique within the database.
5. `idempotency_key` is unique for decisions and for outbox records.
6. A delivery retry must not create a second decision or a second outbox record.
7. A `SENT` record must not be delivered again by ordinary polling.
8. A worker must not hold a database transaction open while performing network I/O.
9. A `PROCESSING` lease must have an expiry or recovery mechanism so abandoned work can be reclaimed.
10. State transitions must be auditable and must preserve the last error and attempt count.

## Required delivery metadata

The operational outbox implementation must eventually persist:

- `status`
- `attempt_count`
- `next_attempt_at`
- `locked_until`
- `last_error`
- `sent_at`
- `updated_at`

All timestamps must be stored as UTC, preferably in a canonical ISO-8601 representation.

## Retry policy requirements

The production policy must explicitly define:

- maximum attempts;
- retryable versus terminal errors;
- backoff formula and maximum delay;
- lease duration;
- dead-letter transition behavior;
- manual replay procedure for dead-letter records.

Until these values and the corresponding implementation/tests exist, durable outbox delivery is **NOT VERIFIED**.

## Non-goals

This contract does not authorize or describe automatic trading, order placement,
position management, exchange execution, or any other transaction against a
trading venue.
