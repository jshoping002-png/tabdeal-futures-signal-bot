# Outbox Observability Contract

This contract applies only to signal-notification delivery. It does **not** authorize order submission, trading, or exchange execution.

## Required counters

A worker implementation should expose monotonic counters for:

- `outbox_claimed_total`
- `outbox_sent_total`
- `outbox_retry_total`
- `outbox_dead_letter_total`
- `outbox_quarantined_total`
- `outbox_transport_failure_total`
- `outbox_transport_timeout_total`
- `outbox_lease_recovered_total`

Counters should be incremented only after the corresponding persistence transition succeeds. A failed database transition must not be reported as completed.

## Required gauges

The service should expose gauges for:

- `outbox_pending_count`
- `outbox_processing_count`
- `outbox_retry_count`
- `outbox_dead_letter_count`
- `outbox_oldest_eligible_age_seconds`
- `outbox_expired_lease_count`

A missing or unavailable measurement must be represented explicitly as unavailable; it must not be reported as zero.

## Event attributes

Structured logs for each worker outcome should include, where available:

- `event_id` (never a secret);
- `idempotency_key` only when policy permits it;
- lifecycle transition;
- attempt count;
- error class and bounded error message;
- elapsed processing time;
- whether the record was quarantined;
- worker instance identifier.

Payloads, bot tokens, authorization headers, and other credentials must not be logged.

## Alerting recommendations

Operators should consider alerts for:

- sustained growth in `PENDING` or `RETRY`;
- any unexpected growth in `DEAD_LETTER`;
- expired leases above the normal baseline;
- transport timeout spikes;
- oldest eligible record age exceeding the delivery objective;
- inability to read or update the persistence database.

Thresholds must be configured per deployment and are not defined by this contract.

## Verification requirements

Before claiming production readiness, verify in a deployed environment that:

1. every successful state transition emits the matching metric;
2. failed transitions do not emit success metrics;
3. secrets are absent from logs and metric labels;
4. counters survive worker restarts when durable metrics are required;
5. alerts are routed and tested;
6. dashboards distinguish unavailable data from zero.

This document defines requirements only. It does not claim that production metrics, dashboards, or alerts currently exist.

## Safety boundary

Outbox observability must remain limited to persistence and signal-notification delivery. It must never add or conceal order execution, trading endpoints, position management, or exchange actions.
