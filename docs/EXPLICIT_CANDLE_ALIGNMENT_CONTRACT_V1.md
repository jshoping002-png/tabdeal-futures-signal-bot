# Explicit Candle Alignment Contract V1

## Status
DESIGNED — Phase 4

## Purpose
Select the exact candle that is eligible at a decision reference boundary. Alignment is explicit and deterministic; it never repairs or infers market data.

## Selection rule

Given a valid candle series, requested timeframe, and UTC `reference_time`:

1. the series must first pass Series Integrity validation;
2. only candles with `close_time < reference_time` are eligible;
3. a candle with `close_time == reference_time` is not eligible;
4. candles closing after `reference_time` are not eligible;
5. the selected candle is the unique latest eligible candle by `close_time`;
6. if no eligible candle exists, alignment is BLOCKED;
7. if eligibility is ambiguous, alignment is BLOCKED.

## Explicit boundary

Alignment does not infer exchange session boundaries, timezone offsets, missing candles, partial candles, or an alternate timeframe. The requested timeframe must exactly match the candle timeframe and have an explicit duration.

## Point-in-time safety

`reference_time` must be UTC. No wall-clock lookup is allowed. The function may only use the supplied series and reference boundary.

## Failure behavior

Invalid series, invalid timeframe, timezone mismatch, no closed candle, or ambiguous eligibility must fail closed with an explicit reason code.

No sorting-and-accepting, gap filling, interpolation, candle synthesis, fallback timeframe, or nearest-candle substitution is allowed.

## Determinism

Identical input series, timeframe, and reference time produce the identical alignment result and reason codes. No randomness, network, clock, or external mutable state is used.

## Scope exclusions

This contract does not define strategy rules, LONG/SHORT behavior, risk thresholds, provider semantics, persistence, notifications, execution, or retry policy.

## Required tests

- exact close-time boundary rejected;
- future candle excluded;
- latest strictly closed candle selected;
- no closed candle blocks;
- invalid series blocks;
- timeframe mismatch blocks;
- non-UTC reference blocks;
- deterministic repeated selection;
- no nearest/partial fallback.
