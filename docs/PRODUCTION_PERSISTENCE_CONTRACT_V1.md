# Production Persistence Contract V1

## Status

DESIGNED — production storage boundary derived from Phase 11 Persistence and Phase 12 Outbox contracts.

## Objective

Define what a production persistence adapter must guarantee without selecting a database vendor, ORM, schema, or deployment topology.

## Required guarantees

A production persistence implementation MUST satisfy the existing Persistence and Outbox contracts:

1. one atomic transaction for the logical decision and directly associated notification intent;
2. durable idempotency for the logical persistence key;
3. singular logical records under concurrent duplicate requests;
4. exact traceability of snapshot, configuration, decision, signal identity, and notification intent;
5. exact lease ownership for Outbox delivery state transitions;
6. restart-safe state that does not depend on process-local memory;
7. fail-closed behavior when atomicity or ownership cannot be established.

## Database boundary

A concrete database/storage technology may be selected as an adapter implementing these guarantees. The selection MUST document transaction semantics, uniqueness enforcement, durability expectations, migration ownership, connection failure behavior, and recovery behavior.

No vendor, schema, isolation level, retention period, or deployment topology is prescribed by this contract.

## Failure behavior

A storage failure MUST be distinguishable from a committed decision. Partial decision/outbox state MUST NOT be reported as successful persistence.

Concurrent requests using the same logical idempotency key MUST converge to one logical result. A stale worker MUST NOT be able to overwrite a newer lease owner.

## Security

Credentials and connection material are runtime secrets only. They MUST NOT appear in source, fixtures, snapshots, logs, exception messages, or persisted business records.

## Relationship to existing contracts

- Phase 11 `PERSISTENCE_CONTRACT_V1.md` defines the logical persistence behavior.
- `OUTBOX_STORAGE_CONTRACT.md` defines leased storage behavior.
- Phase 12 `OUTBOX_CONTRACT_V1.md` defines notification intent semantics.
- This contract defines the production-adapter acceptance boundary between those logical contracts and a concrete storage technology.

## Non-goals

- selecting PostgreSQL, SQLite, Redis, or another vendor;
- defining a schema or migration framework;
- defining queue/broker behavior;
- defining retry/backoff;
- notification-provider behavior;
- trading execution.

## Acceptance

A production adapter is not GREEN until integration tests demonstrate atomicity, durable idempotency, concurrent duplicate protection, lease ownership, restart recovery, failure handling, and secret-safe logging against the selected storage technology.
