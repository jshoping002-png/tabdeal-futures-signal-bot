# Outbox Storage Contract

## Scope

This document defines the technology-neutral storage contract for leased outbox delivery. It does not select a database, storage engine, schema, ORM, isolation level, or deployment topology.

## Enqueue

`OutboxRepository.enqueue(message)` MUST persist the notification intent atomically with the logical persistence operation described by `PERSISTENCE_CONTRACT.md`.

For a new `idempotency_key`, `enqueue` returns `True`.

For an already-persisted `idempotency_key`, `enqueue` returns `False` and MUST NOT create a second logical notification intent.

The implementation MUST NOT report a successful new enqueue when only part of the surrounding logical persistence transaction is committed.

## Lease acquisition

`OutboxLeaseRepository.acquire_lease(...)` MUST return either one `OutboxLease` representing exclusive ownership or `None` when ownership cannot be safely acquired.

An acquired lease MUST identify exactly one `event_id`, one `owner_id`, and one opaque `lease_token`, with explicit `acquired_at` and `expires_at` timestamps.

The repository MUST NOT expose two simultaneously valid leases as ownership of the same pending event.

Lease acquisition policy, duration defaults, retry policy, and reclamation policy are not defined by this contract.

## Exact lease ownership

`OutboxRepository.mark_delivered(event_id, lease)` MUST change delivery state only when the supplied lease still represents the exact ownership record for that event.

A stale, expired, replaced, mismatched, or otherwise non-owning lease MUST NOT mark an event delivered.

The transition MUST be atomic at the storage boundary so a stale worker cannot overwrite a newer owner's state.

## Release

`OutboxLeaseRepository.release_lease(lease)` MUST release only the exact lease represented by its token. A stale or different lease MUST NOT release another worker's ownership.

## Concurrency and restart safety

Concurrent workers MUST NOT both obtain valid ownership of the same pending event.

A worker restart MUST NOT cause a stale lease to regain ownership after another valid lease has replaced it.

The storage implementation MUST preserve the ownership checks required by `mark_delivered` across concurrent workers and process restarts.

## Failure-closed behavior

If the storage layer cannot establish safe ownership or cannot prove that the supplied lease still owns the event, the operation MUST NOT report a successful state transition.

No fallback ownership or implicit lease inference is permitted.

## Explicit non-goals

This contract does not define:

- database technology or schema;
- SQL statements or ORM behavior;
- transaction/isolation configuration beyond the atomic outcomes required above;
- lease duration defaults;
- retry counts or backoff;
- notification provider behavior;
- exchange order execution or auto-trading.
