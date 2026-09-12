# Tabdeal Futures Signal Bot

Clean-slate implementation of a deterministic crypto perpetual-futures signal and alert engine.

## Engineering principles

- Safety and correctness before speed.
- Point-in-time data only; no lookahead.
- Closed-candle decision boundaries.
- Independent LONG and SHORT decision paths.
- Deterministic, replayable, auditable decisions.
- Fail closed on critical uncertainty or invalid data.
- Idempotent decisions and notifications.
- No auto-trading.
- No runtime market/generated data in Git.
- No runtime Git mutations.
- Public, free-first infrastructure; no paid dependency without explicit approval.

## Scope

The system produces and alerts on trading signals. Execution of trades is explicitly out of scope.

## Status

Phases 1–6 foundations and the LONG/SHORT isolation + Conflict Gate contracts are implemented and under gated engineering verification. Production readiness has not been declared.
