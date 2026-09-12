# Architecture — Phase 6

## Scope

The system is a signal/alert engine only. Order execution and auto-trading are out of scope.

## Decision pipeline

Data Source → Validation → Point-in-Time Snapshot → Series Integrity → Explicit Candle Alignment → Strategy Evaluation → LONG / SHORT Isolation → Conflict Gate → Risk Gate → Decision → Persistence/Outbox → Notification

Each boundary has an explicit contract. Invalid or uncertain critical input fails closed.

## Core invariants

1. Decisions use only information available at or before the decision time.
2. Only closed candles may enter a signal decision.
3. A snapshot is immutable once created.
4. Candle series must not contain gaps, overlaps, invalid durations, or ambiguous timeframe semantics.
5. Candle boundary alignment must be explicitly supplied; exchange/session anchoring is never inferred.
6. LONG and SHORT evaluation paths do not consume each other's outputs.
7. Conflict Gate is the only component allowed to compare LONG vs SHORT outcomes.
8. A deterministic input snapshot plus deterministic config produces one deterministic result.
9. Critical failures produce no signal.
10. Signal identity must be idempotent.
11. Runtime data and generated artifacts never belong in Git.
12. Runtime never mutates Git.

## Phase 6 — Explicit Candle Alignment Contract

### Responsibilities

- Require an explicit UTC anchor time for candle-boundary validation.
- Validate that a candle's declared timeframe matches the policy timeframe.
- Validate that candle open times fall exactly on the explicit timeframe boundary defined by the supplied anchor.
- Reject non-UTC candle timestamps at the alignment boundary.
- Return stable, deterministic reason codes without inferring an exchange or session calendar.

### Contract

`AlignmentPolicy` binds a fixed-duration `TimeframeSpec` to an explicit UTC `anchor_time`.

`AlignmentPolicy.contains()` accepts only candles whose timeframe matches the policy and whose open time is an exact duration multiple from the anchor.

`validate_alignment()` is pure and deterministic. It does not infer exchange-specific anchors, sessions, holidays, funding windows, or calendar semantics.

### Explicit boundary

Phase 6 does not define an exchange adapter, exchange-specific session/calendar rules, multi-timeframe parent-child mapping, indicator calculations, risk rules, or trading rules. Those require separate explicit contracts and must not be inferred.
