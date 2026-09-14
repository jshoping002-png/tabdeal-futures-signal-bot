# Data Source Contract V1

## Status

IMPLEMENTED — Phase 1 market-data source and ingestion boundary.

## Objective

Define the first pipeline boundary that receives a point-in-time market-data request and returns a `MarketSnapshot` without introducing exchange-specific behavior that has not been contracted.

## Request

A `SnapshotRequest` explicitly contains:

- requested symbols;
- requested timeframes;
- UTC `reference_time`.

Symbols and timeframes are immutable tuples, non-empty, and duplicate-free. `reference_time` must be UTC.

## Source

`MarketDataSource` is the technology-neutral source interface. Every source exposes a non-empty `source_id` and implements:

`source.snapshot(request) -> MarketSnapshot`

The source response must identify the same source, preserve the requested reference time, remain inside the requested symbol/timeframe scope, and contain only data available strictly before the reference time.

## Ingestion

`ingest()` is the fail-closed boundary between a source and the rest of the decision pipeline. It:

1. validates the request and source interface;
2. receives one snapshot from the source;
3. verifies source identity;
4. verifies requested symbol/timeframe scope;
5. runs the existing snapshot validation;
6. returns an immutable `IngestionResult` only when validation succeeds.

Any failure raises `MarketDataIngestionError` or the source's explicit unavailable-data error. No fallback, repair, trimming, inference, or lookahead is permitted.

## Deterministic reference implementation

`InMemoryMarketDataSource` is a deterministic source implementation for unit tests and replay fixtures. It does not simulate an exchange and does not generate market data. Snapshots must be explicitly registered and are returned only for the exact `SnapshotRequest` key.

This reference implementation is not a claim that a production exchange adapter exists.

## Production provider boundary

No live exchange/provider adapter is introduced in V1 because the repository specification does not define a provider API, authentication contract, endpoint semantics, rate limits, pagination, reconnect behavior, or provider-specific timeframe/session rules. Inventing those details would violate fail-closed and no-guessing requirements.

A production provider adapter can implement `MarketDataSource` once its external provider contract is explicitly selected and verified.

## Safety invariants

- UTC timestamps only.
- Closed candles only: `close_time < reference_time`.
- No future data.
- No silent repair or inference.
- Immutable snapshots.
- Deterministic source identity and request scope.
- Runtime source code does not mutate Git or persist secrets.
- No order execution or auto-trading.

## Acceptance

Phase 1 source/ingestion acceptance requires unit and failure-path coverage for source identity, exact request scope, missing data, duplicate registration, deterministic retrieval, and point-in-time validation, followed by GREEN CI.
