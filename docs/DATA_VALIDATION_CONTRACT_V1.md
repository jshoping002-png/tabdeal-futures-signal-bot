# Data Validation Contract V1

## Status

IMPLEMENTED — Phase 2 validation boundary.

## Objective

Validate received market data before it enters the deterministic decision pipeline. Validation is limited to schema/data-quality and request-scope safety; it does not perform series repair, candle alignment, strategy evaluation, risk decisions, or notification behavior.

## Input contract

`validate_snapshot(request, snapshot)` accepts only a `SnapshotRequest` and a `MarketSnapshot`.

The existing domain/data constructors enforce the structural schema before validation:

- symbols and timeframes are non-empty, duplicate-free tuples;
- timestamps are timezone-aware UTC datetimes;
- candle timestamps have positive duration;
- OHLCV values are numeric and finite;
- prices are positive and OHLC bounds are valid;
- volume is non-negative;
- snapshots are immutable, non-empty, duplicate-free, and deterministically ordered;
- snapshot candles are unavailable to the decision before their close time and therefore must satisfy `close_time < reference_time`;
- snapshot identity and source identity are non-empty.

Validation must not silently repair malformed objects.

## Validation rules

The validation boundary must reject/block:

1. request/reference-time mismatch;
2. missing requested symbol/timeframe pairs;
3. unrequested symbol/timeframe pairs;
4. any candle that is not point-in-time available at the request reference time;
5. any invalid numeric/value condition that reaches the validation boundary despite the domain constructor protections.

Validation results are deterministic and contain explicit issue codes. The same request and snapshot produce the same report.

## Ownership boundaries

Phase 2 owns validation of received data. The following remain separate:

- **Phase 3:** immutable point-in-time snapshot semantics;
- **Phase 4:** series continuity, gaps, overlaps, and completeness across candle sequences;
- **Phase 5:** temporal/candle integrity and boundary rules beyond basic validation;
- **Phase 6:** explicit candle alignment;
- **Phases 7–10:** strategy, side isolation, conflict, risk, and final decision;
- **Phase 11:** persistence;
- **Phase 12+:** Outbox, delivery, providers, retry, and optional broker infrastructure.

Validation must never infer missing data, fill gaps, trim records to hide errors, or normalize ambiguous timeframe/session semantics.

## Fail-closed behavior

Invalid or ambiguous critical input produces an invalid `ValidationReport`. No signal may be produced from an invalid report.

No network, wall clock, randomness, fallback source, or external mutable state is permitted.

## Acceptance

Phase 2 acceptance requires unit and boundary tests covering valid data, missing requested data, unrequested data, malformed/invalid values, point-in-time violations, type-boundary rejection, deterministic issue reporting, and regression coverage, followed by GREEN CI for the exact implementation commit.
