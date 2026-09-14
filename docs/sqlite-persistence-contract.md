# SQLite persistence contract

## Scope

This document defines the first durable-storage increment for the signal pipeline. It does **not** add order placement, execution, exchange-side actions, or automated trading.

## Stored records

The adapter stores every accepted decision in `decisions`. Decisions with status `SIGNAL` additionally produce one durable notification record in `outbox`.

`BLOCKED` decisions are persisted for auditability, but do not create an outbox notification.

## Atomicity

The decision row and, when applicable, its outbox row are inserted in one SQLite transaction. If either insert fails, neither record may remain committed.

## Idempotency

- `idempotency_key` is unique in `decisions`.
- `event_id` is unique in `outbox`.
- Repeating the same request must return an idempotent replay result and must not create another decision or outbox row.
- Reusing an existing `idempotency_key` with a different request payload is a collision and must fail explicitly; it must never silently overwrite data.

## Outbox semantics

The outbox is durable and initially contains pending messages. Delivery, retry, leasing, dead-letter handling, and provider-specific transport remain separate follow-up increments.

The adapter must not mark a message delivered merely because it was inserted into SQLite.

## Time and replay requirements

All persisted timestamps must retain their UTC meaning. The stored context must preserve `decision_time`, `reference_time`, `snapshot_id`, and `config_version`; this is required for audit and replayability.

## Non-goals

This increment does not:

- submit orders;
- manage positions;
- connect to an exchange for execution;
- infer missing context;
- bypass existing domain validation;
- replace the in-memory reference adapters.
