# Architecture — Phase 5

## Scope

The system is a signal/alert engine only. Order execution and auto-trading are out of scope.

## Decision pipeline

Data Source → Validation → Point-in-Time Snapshot → Series Integrity → Strategy Evaluation → LONG / SHORT Isolation → Conflict Gate → Risk Gate → Decision → Persistence/Outbox → Notification

Each boundary has an explicit contract. Invalid or uncertain critical input fails closed.

## Core invariants

1. Decisions use only information available at or before the decision time.
2. Only closed candles may enter a signal decision.
3. A snapshot is immutable once created.
4. Candle series must not contain gaps, overlaps, invalid durations, or ambiguous timeframe semantics.
5. LONG and SHORT evaluation paths do not consume each other's outputs.
6. Conflict Gate is the only component allowed to compare LONG vs SHORT outcomes.
7. A deterministic input snapshot plus deterministic config produces one deterministic result.
8. Critical failures produce no signal.
9. Signal identity must be idempotent.
10. Runtime data and generated artifacts never belong in Git.
11. Runtime never mutates Git.

## Phase 5 — Candle Series Integrity Contract

### Responsibilities

- Define explicit, fixed-duration timeframe semantics for minute/hour/day/week units.
- Reject ambiguous calendar-month timeframes instead of guessing their duration.
- Validate candle duration against the declared timeframe.
- Detect non-deterministic ordering, overlapping candles, and gaps between adjacent candles.
- Validate each symbol's series independently so no LONG/SHORT cross-talk is introduced.
- Keep series validation pure and deterministic.

### Contract

`TimeframeSpec.parse()` converts only explicitly supported fixed-duration timeframe codes into a `timedelta`.

`SeriesIntegrityReport` is immutable. A valid report has no reason codes; an invalid report has one or more stable reason codes.

`validate_candle_series()` validates one ordered candle series. `validate_snapshot_series()` applies the same integrity boundary independently to each symbol in a snapshot.

### Explicit boundary

Phase 5 does not define exchange-specific candle anchoring, timezone/session calendars, market holidays, funding events, indicator calculations, or trading rules. Those require explicit contracts and must not be inferred from a generic timeframe string.
