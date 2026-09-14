# Phase 1–2 Source Boundary

## Phase 1 — Data Source / Ingestion

Owns provider connectivity and raw-to-domain ingestion. Approved source classes are defined by `MARKET_INFORMATION_SOURCES_CONTRACT_V1.md`. Phase 1 must not decide whether data is valid for a signal.

Responsibilities:
- provider adapter;
- public endpoint access;
- transport/schema mapping;
- source identity;
- source timestamps and availability metadata;
- ingestion into the domain boundary.

## Phase 2 — Validation

Owns acceptance/rejection of received data. It validates schema, types, timestamps, scope, OHLCV integrity, completeness and other contracted quality constraints. It does not contain provider transport behavior or strategy semantics.

## Boundary

`Provider → Phase 1 Source Adapter/Ingestion → Phase 2 Validation → Phase 3 PIT Snapshot`

Source disagreement, unavailable timing metadata, unsupported provider behavior, or invalid data must not be repaired or inferred silently.

## Activation rule

A source listed in the inventory is not automatically production-active. Each provider requires verified public unauthenticated endpoint behavior and a provider-specific contract before implementation/activation.

## No strategy invention

Source presence never creates a trading rule. Whale, derivatives, macro, risk, news, and market-context observations remain information inputs until an explicit downstream contract assigns semantics.
