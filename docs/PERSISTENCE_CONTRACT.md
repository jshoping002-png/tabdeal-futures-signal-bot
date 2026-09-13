# Persistence Contract

## Scope

This document defines the technology-neutral contract for persisting one final signal decision and its notification intent. It does not select a database, storage engine, schema, ORM, or deployment topology.

## Atomicity

A persistence operation is one logical transaction:

`FinalDecision + associated Signal state + associated Outbox state`

The implementation MUST NOT report `persisted=True` if only part of that logical transaction was committed. A failure MUST NOT be exposed as a successful partial persistence result.

The storage boundary is responsible for making the transaction atomic; callers must not assemble a decision and outbox write as separate successful operations.

## Idempotency

Every persistence request MUST carry a non-empty `idempotency_key`.

For a new key, the implementation returns:

- `persisted=True`
- `idempotent_replay=False`

Repeating the same logical request with an already-persisted key MUST NOT create a duplicate logical decision or notification intent. The implementation returns:

- `persisted=True`
- `idempotent_replay=True`

A replay is therefore a successful persisted outcome, not a failure or a second write.

## Consistency of the idempotency key

The idempotency key identifies the logical persistence operation. Implementations MUST NOT treat a repeated key as a new logical decision.

The contract does not define how keys are generated, normalized, stored, or indexed. Those details require a separate storage implementation contract.

## Failure-closed behavior

Invalid persistence requests MUST be rejected before persistence is attempted. In particular:

- context must be a valid `DecisionContext`;
- decision must be a valid `FinalDecision`;
- idempotency key must be a non-empty string.

A persistence result MUST be internally consistent. `idempotent_replay=True` requires `persisted=True`.

## Transaction boundary

The persistence implementation MUST own the transaction boundary required to guarantee the atomicity described above. No specific transaction API or storage technology is prescribed by this contract.

## Outbox relationship

When a notification intent is required by the persisted decision, its creation belongs to the same atomic persistence boundary. Delivery is a separate concern handled by the outbox/notification layer after persistence.

Persistence success therefore means the logical decision and its associated notification intent are durably represented together; it does not mean that notification delivery has succeeded.

## Explicit non-goals

This contract does not define:

- database technology or schema;
- connection pooling or migration strategy;
- retry counts, backoff, or timeout defaults;
- lease acquisition policy;
- notification provider behavior;
- exchange order execution or auto-trading.

Those behaviors require their own explicit contracts before implementation.
