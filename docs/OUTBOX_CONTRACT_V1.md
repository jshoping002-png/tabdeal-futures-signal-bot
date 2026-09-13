# Outbox Contract V1

**Status:** DESIGNED

**Phase:** 12 — Outbox / Notification Intent

## Objective

Define the existing outbox boundary so notification intent is persisted deterministically, idempotently, and safely under concurrent workers and stale leases.

This contract is derived from the existing outbox, lease/reliability, notification-dispatcher boundaries, and repository tests. It does not introduce a new retry policy, provider, database technology, or trading behavior.

## 1. Outbox message

An outbox message is an immutable notification intent associated with one `DecisionContext` and one `FinalDecision`.

Required fields:

- `event_id`
- `idempotency_key`
- `context`
- `decision`
- `created_at`
- `status`, initially `PENDING`

The message preserves decision/context traceability. Invalid message types or required fields are rejected.

## 2. Enqueue and idempotency

`enqueue()` is atomic within the outbox repository.

- A new idempotency key creates exactly one pending message.
- Re-enqueueing the same idempotency key with the same message is an idempotent duplicate and must not create another record.
- Reusing an idempotency key with a different message is an idempotency collision and must fail closed.
- Duplicate logical events must not be created.

## 3. Delivery state

Messages start as `PENDING`.

A message may become `DELIVERED` only through the controlled delivery path using the exact lease that owns the event.

No additional outbox status transition is introduced by this contract.

## 4. Lease ownership

Outbox processing uses an exclusive per-event lease.

- A worker may acquire a lease only when the event exists and no currently active lease owns it.
- Concurrent active acquisition for the same event must not grant two workers ownership.
- Lease identity contains the event, owner, token, acquisition time, and expiration time as defined by the existing reliability contract.
- An expired/stale lease may be replaced according to the existing acquisition-time/expiration semantics.
- A delivery mutation requires the exact current lease; a stale or different lease must not mutate delivery state.
- Releasing a stale lease must not release another worker's current lease.

## 5. Notification outcome boundary

The notification dispatcher defines the delivery transition:

- `DELIVERED` and `DUPLICATE` outcomes permit the outbox event to be marked delivered.
- `RETRYABLE` and `BLOCKED` outcomes leave the outbox message pending.

This contract does not invent retry counts, backoff durations, scheduling, or provider selection.

## 6. Determinism and fail-closed behavior

The same valid message, idempotency key, and lease state must produce deterministic repository behavior.

Missing or invalid context, decision, identifiers, or ownership is rejected rather than inferred or repaired.

No randomization, fallback direction, or external market state is used by the outbox.

## 7. Runtime and security safety

- Outbox processing must not mutate the Git repository.
- Secrets must not be persisted into source, logs, snapshots, or test fixtures.
- The outbox is for notification intent only; it does not execute trades or manage positions.

## 8. Scope exclusions

This contract does not select:

- database/vendor technology
- production schema or migrations
- queue/broker technology
- retention policy
- retry/backoff policy
- Telegram or another notification provider
- leverage, sizing, stop-loss/take-profit, funding, or execution behavior

## Acceptance criteria

Implementation must have unit/contract tests for:

- enqueue and idempotency
- idempotency collision
- delivery ownership
- stale and concurrent lease behavior
- notification outcome handling
- determinism
- failure paths
- regression behavior

CI must be GREEN before advancing to the next logical change.
