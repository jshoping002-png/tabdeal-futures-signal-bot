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

- **Phase 1:** Data Source / Ingestion — implemented and CI verified.
- **Phase 2:** Validation — next audit/verification target.
- **Phases 3–10:** PIT/temporal integrity, strategy, LONG/SHORT isolation, conflict, risk, final decision and signal identity — implemented contracts with gated verification status recorded in repository history.
- **Phase 11:** Persistence — logical atomic/idempotent contract and in-memory reference implementation exist; production storage adapter remains to be implemented and verified.
- **Phase 12:** Outbox / Notification Intent — contract, leased in-memory reference implementation, and dispatcher boundary exist; production delivery remains separate.
- **Notification Delivery:** provider boundary is defined; Telegram requires a provider-specific implementation contract before implementation.
- **Reliability:** retry-policy boundary is defined; numeric retry/backoff/scheduling values are not invented until explicitly approved.
- **Queue/Broker:** optional boundary is defined; no broker technology is required or selected by default.

## Important boundaries

### Market-data provider

A concrete exchange/provider adapter implements `MarketDataSource` behind the Phase 1 boundary. Provider API, authentication, rate limits, pagination, reconnect behavior, and provider-specific semantics must be explicitly selected and verified.

### Production database/storage

A concrete production persistence adapter implements the Phase 11 guarantees. Database vendor, schema, migrations, and deployment topology are separate implementation decisions.

### Outbox

Phase 12 persists notification intent and protects delivery with idempotency and lease ownership. It does not select Telegram, a database, a broker, or a retry algorithm.

### Telegram / notification provider

Telegram is a concrete notification provider behind the transport-neutral notification boundary. Its API/auth/configuration/error mapping must be explicitly contracted before production implementation.

### Retry policy

Retry decisions are a reliability concern and are separate from provider and Outbox semantics. The retry contract currently defines the boundary and fail-closed behavior without inventing retry counts or backoff values.

### Queue / broker

A queue/broker is optional infrastructure, not a business-logic requirement. If selected, it must preserve Outbox identity, idempotency, lease ownership, and restart safety.

## Security and operational scope

Production readiness additionally requires runtime configuration, secret-safe logging, health/observability, failure recovery, integration testing, and operational verification. These are not claimed complete merely because the domain contracts are implemented.

## Status

**Production readiness: NOT VERIFIED.**

The repository must not be described as production-ready until the remaining production adapters, runtime/operational requirements, replay/backtest verification, security checks, and required CI evidence are complete.
