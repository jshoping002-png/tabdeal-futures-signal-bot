# Architecture — System Scope and Boundaries

## Scope

The system is a deterministic signal/alert engine. Order execution and auto-trading are explicitly out of scope.

## Decision pipeline

`Data Source → Validation → Point-in-Time Snapshot → Series Integrity → Explicit Candle Alignment → Strategy Evaluation → LONG / SHORT Isolation → Conflict Gate → Risk Gate → Decision → Persistence → Outbox → Delivery Worker → Notification Provider`

The queue/broker is optional infrastructure between Outbox and the delivery worker. It is not part of the decision path and is not required unless a separately approved deployment design needs it.

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
11. Persistence and Outbox state must remain atomic and traceable according to their contracts.
12. Delivery must use exact lease ownership and must be idempotent under redelivery.
13. Runtime data and generated artifacts never belong in Git.
14. Runtime never mutates Git.
15. Secrets are runtime-only and must not enter source, fixtures, logs, snapshots, or business records.

## Boundary ownership

### Phase 1 — Data Source / Ingestion

`MarketDataSource` is the technology-neutral market-data boundary. A real exchange/provider adapter belongs behind this interface and requires its own verified external-provider contract before production activation.

The source roadmap includes public/no-API-key candidates such as Binance, Bybit, OKX, Kraken, Coinbase Exchange, and Deribit for market/derivatives data. This is a source inventory, not an activation claim; provider-specific endpoints, timestamps, availability semantics, limits, and operational behavior must be verified before implementation.

Macro/economic and external intelligence sources are separate from the market-data transport boundary. Public/no-key sources are preferred where their published API permits programmatic access. They must not be converted into strategy rules without a separate domain contract.

### Phase 2 — Validation

Validates received data according to the existing data/domain contracts. Provider-specific transport behavior does not belong here.

### Phase 3 — Point-in-Time Snapshot

The PIT snapshot boundary is defined by `PIT_SNAPSHOT_CONTRACT_V1.md`. It creates the immutable temporal view consumed by downstream decision stages and enforces the strict closed-candle rule `close_time < reference_time`.

### Phases 4–10 — Decision pipeline

Series integrity, candle alignment, strategy, LONG/SHORT isolation, conflict, risk, final decision, and signal identity remain deterministic and provider/storage independent.

### Phase 11 — Persistence

The logical persistence contract defines atomic decision + associated notification intent, durable idempotency, traceability, concurrency safety, and fail-closed behavior. A production database/storage adapter belongs behind that contract and must satisfy `PRODUCTION_PERSISTENCE_CONTRACT_V1.md`.

### Phase 12 — Outbox / Notification Intent

Outbox owns durable notification intent, idempotency, delivery state, and lease ownership. It deliberately does not choose a database, queue/broker, retry policy, or notification provider.

### Notification Delivery — Provider boundary

The delivery worker invokes the technology-neutral `NotificationSender`. A concrete provider, including Telegram, belongs behind `NOTIFICATION_PROVIDER_CONTRACT_V1.md`. Provider-specific API/auth/rate-limit behavior must be explicitly contracted before implementation.

### Reliability — Retry policy

Retry decisions belong to `RETRY_POLICY_CONTRACT_V1.md`. Retry policy is separate from strategy, risk, persistence, Outbox storage, and provider implementation. Numeric retry limits, backoff, scheduling, and time windows require explicit approval before production activation.

### Optional Infrastructure — Queue / Broker

If asynchronous transport is needed, it belongs between Outbox and the delivery worker and must satisfy `QUEUE_BROKER_BOUNDARY.md`. A queue/broker is not mandatory and must not silently redefine retry or persistence semantics.

## External intelligence boundary

Market analysis may eventually consume multiple information classes: exchange market/derivatives data, order flow/liquidity, on-chain and whale activity, macro/economic events, risk indicators, and news/events. These sources are inputs to an intelligence layer; they are not automatically trading rules.

For every source, the implementation must preserve point-in-time semantics, provenance, availability timestamps, validation status, and fail-closed behavior. A provider requiring API keys or paid credentials is not an eligible source for the current no-key source set unless separately approved.

No external intelligence source may silently override the Strategy Contract, Risk Policy Contract, or Conflict Gate.

## Explicit non-goals

- exchange order execution;
- automatic buy/sell;
- position opening/closing;
- leverage, sizing, stop-loss/take-profit, funding, or execution behavior unless separately contracted as signal-domain behavior;
- inventing provider-specific APIs or operational defaults;
- committing secrets or runtime data to Git.

## Contract map

| Boundary | Contract | Status |
| --- | --- | --- |
| Market data source / ingestion | `DATA_SOURCE_CONTRACT_V1.md` | IMPLEMENTED |
| Data provider/source inventory | Architecture source inventory | DESIGNED |
| Point-in-Time snapshot | `PIT_SNAPSHOT_CONTRACT_V1.md` | DESIGNED / IMPLEMENTED boundary |
| Decision / signal identity | `DECISION_IDENTITY_V1.md` | DESIGNED / IMPLEMENTED |
| Persistence | `PERSISTENCE_CONTRACT_V1.md` | DESIGNED / IMPLEMENTED reference |
| Production persistence adapter | `PRODUCTION_PERSISTENCE_CONTRACT_V1.md` | DESIGNED |
| Outbox | `OUTBOX_CONTRACT_V1.md` | DESIGNED / IMPLEMENTED |
| Outbox storage / lease | `OUTBOX_STORAGE_CONTRACT.md` | DESIGNED / IMPLEMENTED reference |
| Notification provider | `NOTIFICATION_PROVIDER_CONTRACT_V1.md` | DESIGNED |
| Retry policy | `RETRY_POLICY_CONTRACT_V1.md` | DESIGNED |
| Queue / broker | `QUEUE_BROKER_BOUNDARY.md` | DESIGNED / OPTIONAL |

These contracts define boundaries; they do not claim that every production adapter is already implemented. Production readiness requires the relevant adapter implementation, integration tests, operational verification, and GREEN CI evidence.
