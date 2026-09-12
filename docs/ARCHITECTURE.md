# Architecture — Phase 1

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

Phase 1 establishes the domain contracts and repository safety boundary. Market adapters, indicators, strategy rules, persistence, Telegram delivery, scheduling, and production deployment are intentionally deferred until their contracts are designed and gated.
