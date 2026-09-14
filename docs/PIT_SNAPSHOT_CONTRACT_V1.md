# Point-in-Time Snapshot Contract V1

## Status

DESIGNED — Phase 3 decision-pipeline boundary.

## Objective

Define the immutable point-in-time boundary between validated market data and later decision stages. A snapshot represents only information that was available before its reference time and is the sole market-data view consumed by downstream deterministic decision logic.

## Inputs

`SnapshotRequest` contains:

- an explicit non-empty, duplicate-free tuple of symbols;
- an explicit non-empty, duplicate-free tuple of timeframes;
- a UTC `reference_time`.

No wall-clock lookup, inferred timeframe, implicit symbol expansion, or external state is permitted.

## Snapshot invariants

A `MarketSnapshot` is immutable and contains:

- a non-empty `snapshot_id`;
- a non-empty `source_id`;
- the exact UTC `reference_time` used by the request;
- an immutable tuple of `Candle` values.

The snapshot must reject:

- non-UTC or naive reference times;
- duplicate candles for the same symbol/timeframe/open time;
- non-deterministically ordered candles;
- candles whose `close_time` is not strictly before `reference_time`.

The strict temporal rule is:

`close_time < reference_time`

A candle closing exactly at `reference_time` is not available to the decision and must be rejected from the snapshot.

## Scope

Snapshot construction does not perform series repair, gap filling, candle alignment inference, strategy evaluation, LONG/SHORT comparison, risk decisions, persistence, or notification. Those responsibilities remain in their respective pipeline boundaries.

## Point-in-Time safety

Downstream stages may consume only the snapshot contents. They must not fetch newer data or consult mutable external state while evaluating the same decision.

The snapshot therefore provides a stable temporal boundary for replay and live decision parity:

`source response → validated snapshot → deterministic decision`

## Determinism

For the same explicitly supplied request and source response, snapshot contents and ordering are deterministic. Snapshot identity is supplied by the source/boundary and is not generated from a runtime clock or randomness by this contract.

## Fail-closed behavior

Invalid or ambiguous snapshot input blocks progression. No fallback, trimming, repair, inference, or substitution is permitted.

## Acceptance

Phase 3 acceptance requires tests covering:

- immutable snapshot state;
- UTC reference-time requirements;
- exact-boundary rejection (`close_time == reference_time`);
- future-candle rejection;
- deterministic candle ordering and duplicate rejection;
- request/snapshot reference-time agreement;
- replay-equivalent behavior with identical inputs;
- regression protection for existing validation behavior;
- GREEN CI evidence.

## Explicit exclusions

This contract does not define provider APIs, API keys, rate limits, retries, database schema, queue/broker technology, strategy thresholds, financial risk thresholds, order execution, or notification-provider behavior.
