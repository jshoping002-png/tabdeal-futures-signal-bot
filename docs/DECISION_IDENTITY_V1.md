# Decision & Signal Identity V1

## Status

DESIGNED — Phase 10 contract for deterministic final decisions and signal identity.

## Objective

Define the final decision boundary and a deterministic identity for a logical signal without introducing trading execution or financial policy.

## Final Decision Contract

1. LONG and SHORT arrive from their isolated paths after Conflict Gate and Risk Gate.
2. If both sides are `SIGNAL`, the final result is `BLOCKED` with `CONFLICT_BOTH_DIRECTIONS`.
3. If neither side is `SIGNAL`, the final result is `BLOCKED` with `NO_SIGNAL`, except that an existing conflict block remains `CONFLICT_BOTH_DIRECTIONS`.
4. If exactly one side is `SIGNAL`, the final result is `SIGNAL` and preserves that side's direction and reason code.
5. A `SIGNAL` always carries `signal_id`, `created_at`, `snapshot_id`, `config_version`, direction, and reason code.
6. A `BLOCKED` final result carries no `SignalDecision`.

## Signal Identity

A signal identity is deterministic and represents the logical decision for one validated snapshot/configuration and one direction/reason.

Canonical identity input, in this exact order, is:

`identity-v1 | snapshot_id | config_version | direction | reason_code`

The fields are UTF-8 encoded, joined by the literal separator `|`, and hashed with SHA-256. The lowercase hexadecimal digest is the `signal_id`.

`created_at` is deliberately excluded from identity because it describes creation time, not logical signal identity. Replaying the same decision with a different processing timestamp must therefore resolve to the same identity.

## Idempotency

The generated `signal_id` is suitable as the logical signal idempotency key. Persistence must reject creation of a second logical decision with the same identity and must return the existing logical result as an idempotent replay.

## Fail-Closed Rules

- Missing/blank identity inputs are invalid.
- Unsupported direction or malformed decision data is invalid.
- Identity generation performs no normalization beyond requiring exact string values supplied by the contract.
- No clock, randomness, external state, or fallback participates in identity generation.

## Non-Goals

- order execution;
- position management;
- leverage or exposure limits;
- stop-loss/take-profit;
- notification delivery;
- database schema or storage technology.

## Acceptance

Unit, boundary, determinism, conflict, and regression tests must pass in CI before Phase 10 is promoted.
