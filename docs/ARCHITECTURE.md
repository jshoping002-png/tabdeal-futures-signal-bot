# Architecture — Phase 3

## Scope

The system is a signal/alert engine only. Order execution and auto-trading are out of scope.

## Decision pipeline

Data Source → Validation → Point-in-Time Snapshot → Strategy Evaluation → LONG / SHORT Isolation → Conflict Gate → Risk Gate → Decision → Persistence/Outbox → Notification

Each boundary has an explicit contract. Invalid or uncertain critical input fails closed.

## Core invariants

1. Decisions use only information available at or before the decision time.
2. Only closed candles may enter a signal decision.
3. A snapshot is immutable once created.
4. LONG and SHORT evaluation paths do not consume each other's outputs.
5. Conflict Gate is the only component allowed to compare LONG vs SHORT outcomes.
6. A deterministic input snapshot plus deterministic config produces one deterministic result.
7. Critical failures produce no signal.
8. Signal identity must be idempotent.
9. Runtime data and generated artifacts never belong in Git.
10. Runtime never mutates Git.

## Phase 1 boundary

Phase 1 established the domain contracts and repository safety boundary. Its CI gate is required before advancing later phases.

## Phase 2 — Point-in-Time Market Data Contract

### Responsibilities

- Define the request boundary for symbols, timeframes, and a fixed reference time.
- Define an immutable market snapshot that can be consumed by deterministic strategy code.
- Reject duplicate candles and duplicate request dimensions.
- Reject candles that were not fully closed and available at the snapshot reference time.
- Preserve deterministic candle ordering.
- Keep source identity explicit without coupling the domain to a network/provider implementation.

### Contract

`SnapshotRequest` contains only explicit, UTC-normalized temporal input and unique symbol/timeframe dimensions.

`MarketSnapshot` contains an explicit snapshot ID, source ID, UTC reference time, and an immutable tuple of validated candles.

`MarketDataSource` is a protocol boundary. An implementation must return only data available at the requested reference time and must fail closed when that contract cannot be satisfied.

### Non-goals

Phase 2 does not yet select an exchange API, implement network retries, calculate indicators, fill missing historical data, or define trading strategy rules. Those require separate contracts and gates.

## Phase 3 — Strategy Evaluation Contract

### Responsibilities

- Define the deterministic boundary between an immutable `MarketSnapshot` and strategy evaluation.
- Require the snapshot reference time to exactly match the decision context reference time.
- Represent one independent side evaluation as LONG or SHORT without cross-side state.
- Map strategy eligibility to the existing `SideDecision` contract.
- Require an explicit reason code for every evaluation, including blocked outcomes.
- Keep strategy evaluation free of system-clock, randomness, network timing, scheduler, notification, persistence, and Git concerns.

### Contract

`StrategyEvaluationRequest` contains only the existing `DecisionContext` and immutable `MarketSnapshot`. Construction fails if their reference times differ.

`StrategyEvaluation` is immutable and contains one direction, an eligibility result, and a non-empty reason code. It can be converted to the domain `SideDecision` without changing direction or semantics.

`StrategyEvaluator` is a protocol boundary for a pure side evaluator. Implementations must be deterministic for the same request and must not read the opposite side's result.

### Non-goals

Phase 3 does not define the actual 4H/1H trading rules, indicators, thresholds, exchange adapter, data acquisition, LONG-vs-SHORT conflict resolution, risk filters, persistence, notifications, or scheduling. Those require their own contracts and phase gates.
