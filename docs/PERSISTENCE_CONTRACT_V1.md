# Persistence Contract V1 — Atomic Decision Record

## Status

DESIGNED — Phase 11 contract derived from the existing decision, identity, outbox, and pipeline boundaries.

## Objective

Persist the final decision as an auditable, replayable record without changing strategy semantics or executing trades.

## Atomicity

One persistence operation is the transaction boundary for the final decision and its directly associated persistence state. The operation either commits all required state or commits none of it.

A partial decision record, partial signal record, or partially-created outbox record is not an accepted outcome.

## Idempotency

The logical idempotency key identifies one deterministic decision event. Repeating the same key must not create a second logical decision or duplicate associated state.

An implementation may report an idempotent replay, but the persisted logical state must remain singular.

## Required traceability

The persisted decision must retain the information needed to reconstruct its identity and audit path, including:

- snapshot identity;
- configuration version;
- final decision status and reason code;
- signal identity when the result is SIGNAL;
- signal direction and signal reason when applicable;
- decision creation timestamp when supplied by the decision layer;
- the caller-provided idempotency key.

## Fail-closed behavior

Invalid persistence requests must be rejected. Persistence must not transform BLOCKED into SIGNAL, infer missing values, repair invalid temporal data, or generate alternative identity values.

Persistence failure is not a successful decision. Callers must be able to distinguish committed state from a failed transaction.

## Concurrency and stale workers

Concurrent attempts using the same logical idempotency key must converge to one logical persisted record. Storage-level uniqueness or an equivalent atomic mechanism is required.

The persistence boundary must not rely on process-local state for duplicate protection.

## Runtime safety

Persistence must not write to Git, modify source files, or expose secrets in records, errors, logs, or snapshots.

## Scope exclusions

V1 does not prescribe a database vendor, schema migration framework, queue technology, retention period, or deployment topology.

It does not define order execution, position management, leverage, stop-loss/take-profit, funding, or position sizing.

## Acceptance

- unit tests for valid and invalid requests;
- atomicity/failure tests;
- duplicate/idempotency tests;
- concurrent duplicate protection tests;
- signal/block traceability tests;
- regression tests against final decision and identity behavior;
- CI GREEN before promotion to the next logical phase.
