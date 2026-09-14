# Series Integrity Contract V1

## Status
DESIGNED — Phase 4

## Purpose
Define deterministic integrity checks for candle series before strategy evaluation. This contract owns continuity and timeframe integrity; it does not choose candles for a decision and does not define trading rules.

## Required invariants

A series is valid only when all of the following hold:

1. The series is non-empty.
2. Every item is a valid `Candle`.
3. Every candle belongs to the requested symbol/timeframe scope.
4. Timeframe syntax and duration are explicit and deterministic.
5. Every candle duration exactly equals the requested timeframe duration.
6. Candles are ordered by `open_time`.
7. Candles do not overlap.
8. Adjacent candles are contiguous: `current.open_time == previous.close_time`.
9. Candle timestamps are UTC.
10. Duplicate candle identity is invalid.
11. No implicit gap filling, interpolation, sorting-and-accepting, or timeframe inference is allowed.

## Point-in-time boundary

PIT availability is owned by the Phase 3 snapshot contract. Phase 4 may consume a validated snapshot but must not introduce post-reference data or repair temporal violations.

## Alignment boundary

Phase 4 does not select the latest closed candle, infer exchange/session anchors, or map one timeframe onto another. Those responsibilities belong to the explicit candle-alignment boundary after series integrity.

## Failure behavior

Any integrity violation produces an invalid report with explicit reason codes. The downstream decision path must fail closed and produce no signal from an invalid series.

## Determinism

For identical input candles and requested timeframe, the result and reason-code ordering are identical. No wall clock, randomness, network, or external mutable state is used.

## Required tests

- empty series;
- invalid timeframe;
- timeframe mismatch;
- invalid duration;
- unsorted input;
- duplicate identity;
- overlap;
- gap;
- UTC boundary;
- exact contiguous series;
- deterministic repeated evaluation;
- per-symbol series isolation;
- snapshot integration.

## Exclusions

This contract does not define strategy conditions, LONG/SHORT behavior, risk thresholds, execution, provider-specific transport, retry/backoff, database schema, or notification behavior.
