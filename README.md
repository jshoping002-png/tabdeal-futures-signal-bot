# Tabdeal Futures Signal Bot

Deterministic crypto perpetual-futures signal and alert engine.

## Engineering principles

- Safety and correctness before speed.
- Point-in-time data only; no lookahead.
- Closed-candle decision boundaries.
- Independent LONG and SHORT decision paths.
- Deterministic, replayable, auditable decisions.
- Fail closed on critical uncertainty or invalid data.
- Idempotent decisions and notifications.
- No auto-trading or exchange order execution.
- No runtime market/generated data in Git.
- No runtime Git mutations.
- Secrets are runtime-only.

## Reference pipeline

`Data Source → Validation → Point-in-Time Snapshot → Series Integrity → Explicit Candle Alignment → Strategy Evaluation → LONG / SHORT Isolation → Conflict Gate → Risk Gate → Decision → Persistence → Outbox → Delivery Worker → Notification Provider`

Queue/broker infrastructure is optional and belongs between Outbox and the delivery worker only when explicitly selected.

## Current contract map

- **Phase 1:** Data Source / Ingestion — implemented; CI verification status must be checked from repository workflow evidence.
- **Phase 2:** Validation — audit/verification target.
- **Phases 3–10:** PIT/temporal integrity, strategy, LONG/SHORT isolation, conflict, risk, final decision and signal identity — implemented contracts with gated verification status recorded in repository history.
- **Phase 11:** Persistence — atomic/idempotent persistence contract, SQLite adapter, schema, replay/collision handling, and tests exist. Production deployment and operational verification remain incomplete.
- **Phase 12:** Outbox / Notification Intent — SQLite-backed lifecycle exists with claim, lease recovery, retry, sent, and dead-letter transitions. Durable production operation and recovery testing remain to be verified.
- **Notification Delivery:** transport boundary, deterministic formatter, Telegram configuration contract, and notification worker exist. A production Telegram provider and end-to-end delivery verification remain separate tasks.
- **Reliability:** bounded worker retry behavior exists, but operational retry policy, alerting, and failure-management procedures require explicit verification.
- **Queue/Broker:** optional boundary is defined; no broker technology is required or selected by default.

## Important boundaries

### Market-data provider

A concrete exchange/provider adapter implements `MarketDataSource` behind the Phase 1 boundary. Provider API, authentication, rate limits, pagination, reconnect behavior, and provider-specific semantics must be explicitly selected and verified.

### Production database/storage

The repository contains a SQLite persistence adapter for atomic decision storage and signal outbox creation. Production database selection, migrations, backups, deployment topology, concurrency characteristics, and operational recovery remain separate implementation and verification decisions.

### Outbox

The outbox persists notification intent and protects delivery with idempotency and lease ownership. Its lifecycle includes pending, processing, retry, sent, and dead-letter states. It does not select Telegram, a broker, or a production deployment topology.

### Telegram / notification provider

Telegram is a concrete notification provider behind the transport-neutral notification boundary. Its API/authentication, configuration, timeout behavior, error mapping, and end-to-end delivery must be explicitly contracted and verified before production use.

### Retry policy

Retry decisions are a reliability concern and are separate from provider and Outbox semantics. The worker has bounded retry/backoff behavior, while production retry budgets, alerting, dead-letter operations, and runbook procedures still require verification.

### Queue / broker

A queue/broker is optional infrastructure, not a business-logic requirement. If selected, it must preserve Outbox identity, idempotency, lease ownership, and restart safety.

## Security and operational scope

Production readiness additionally requires runtime configuration, secret-safe logging, health/observability, failure recovery, integration testing, security checks, replay/backtest verification, and operational CI evidence. These are not claimed complete merely because the domain contracts or SQLite adapter are implemented.

## Status

**Production readiness: NOT VERIFIED.**

The repository must not be described as production-ready until the remaining production adapters, runtime/operational requirements, replay/backtest verification, security checks, and required CI evidence are complete.
