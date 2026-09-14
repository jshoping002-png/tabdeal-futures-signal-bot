# Notification Worker Contract

## Scope

The notification worker delivers persisted **signal notifications** from the SQLite outbox. It must never submit orders, execute trades, or call exchange trading endpoints.

## Processing model

1. Claim eligible `PENDING` or due `RETRY` records using a bounded lease.
2. Perform network I/O only through the injected `NotificationTransport`.
3. Mark a successfully delivered record as `SENT`.
4. On a delivery or payload error, either schedule `RETRY` or move the record to `DEAD_LETTER`.
5. Process each claimed event independently so one malformed or failed event does not stop the batch.

## Retry contract

- `attempt_count` is incremented when a record is claimed.
- Retry delay is deterministic and bounded by the configured policy:
  - first failed attempt: `base_backoff_seconds`
  - second failed attempt: `2 * base_backoff_seconds`
  - subsequent delays continue exponentially according to the worker configuration.
- Once the claimed attempt count reaches `max_attempts`, the record is moved to `DEAD_LETTER`.
- Error text is persisted for audit and operational diagnosis.

## Event ID integrity

- Every persisted outbox record must contain a stable, non-empty string `event_id`.
- A blank or whitespace-only string is a malformed identifier. After claim, the worker moves it to `DEAD_LETTER` with the error `invalid event_id: empty or whitespace-only` and does not call the transport.
- A missing or non-string `event_id` cannot safely be finalized through the current event-ID-based persistence methods. Such records require a persistence-level quarantine operation keyed by an internal row identity before production use.
- The worker must not invent a replacement event ID during delivery, because that could break auditability and idempotency.

## Lease and recovery

- Claiming a record changes its state to `PROCESSING` and sets `locked_until`.
- The lease prevents concurrent workers from claiming the same record during the lease window.
- Expired `PROCESSING` records must be recovered to `RETRY` by the persistence layer before or during the next worker cycle.
- Network I/O must never occur while a persistence transaction is open.

## Idempotency

- The worker does not create decisions or outbox records.
- It does not create a new event when retrying.
- `event_id` remains stable across retries.
- `SENT` records are not eligible for another claim.

## Failure classification

The current worker treats transport and payload exceptions uniformly as delivery failures. A production transport adapter should classify terminal errors explicitly before enabling production delivery.

## Observability requirements

A production deployment should expose, at minimum:

- claimed, sent, retried, and dead-lettered counts;
- event ID and idempotency key correlation without secrets;
- attempt count and last error;
- processing latency;
- lease-expiry recovery count;
- queue age and backlog size.

Until a real transport, operational metrics, durable recovery procedure, and integration tests are implemented and verified, production notification delivery remains **NOT VERIFIED**.
