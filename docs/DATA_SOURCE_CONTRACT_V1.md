# Data Source Contract V1

## Status

IMPLEMENTED — Phase 1 market-data source and ingestion boundary.

## Objective

Define the first pipeline boundary that receives point-in-time market-data requests and returns validated market data without introducing uncontracted provider-specific behavior.

## Source classes

The project recognizes two source classes:

1. **Primary market sources** — direct public market-data interfaces from exchanges/providers.
2. **Derived intelligence sources** — public data feeds used to build market, derivatives, whale/on-chain, macro, risk, or news context. These are separate from the core candle source and must have their own contracts before affecting decisions.

## Primary market-source candidates

The initial source registry may evaluate public, no-API-key market-data interfaces from:

- Binance
- Bybit
- OKX
- Kraken
- Coinbase Exchange
- Deribit

The registry does not imply that every source is already production-connected. A provider becomes production-active only after its endpoint, timestamp, availability, rate-limit, pagination, reconnect, symbol, timeframe, and failure semantics are explicitly verified.

## Public-access rule

For the initial project source layer, a provider requiring an API key, API secret, paid credential, or authenticated account for the required data path is excluded from the production source registry unless the project specification is later changed explicitly.

This rule does not prohibit public web pages; it means web-page availability alone is not treated as a programmatic data contract.

## Required market data

A production market source may supply, where publicly available and explicitly contracted:

- OHLCV candles;
- trades;
- ticker/mark/index data;
- order-book depth;
- funding information;
- open interest;
- liquidation information;
- taker/trade-flow information;
- other derivatives fields only when their semantics are verified.

The presence of a field in a provider API does not make it a strategy input. Strategy consumption requires a separate contract.

## Market-intelligence source classes

The architecture reserves explicit boundaries for:

- derivatives and leverage context;
- order flow and liquidity;
- whale and large-transfer activity;
- on-chain/exchange-flow information;
- stablecoin flows;
- options information;
- ETF/institutional flows;
- macro/economic data;
- risk indicators;
- news and event information.

These inputs must not be silently mixed into `MarketSnapshot`. Each class requires its own schema, timestamp/availability semantics, PIT rules, validation, and decision-consumption contract before it can influence Strategy or Risk Gate.

## Current public macro source candidates

Public/no-key candidates include official sources such as:

- U.S. Bureau of Labor Statistics (BLS) public API/data;
- European Central Bank (ECB) public data API.

They may provide unemployment, employment, CPI and other economic series, or monetary/rate data where the public interface exposes them. Exact series identifiers and publication/revision semantics must be verified before implementation.

## Explicit exclusions from this contract

The following are not production source dependencies under the no-key rule:

- CoinGlass API;
- CryptoQuant API;
- Glassnode API;
- FRED API;
- commercial whale/news APIs that require credentials.

Their public websites are not automatically equivalent to public programmatic APIs.

## Request

A `SnapshotRequest` explicitly contains:

- requested symbols;
- requested timeframes;
- UTC `reference_time`.

Symbols and timeframes are immutable tuples, non-empty, and duplicate-free. `reference_time` must be UTC.

## Source interface

`MarketDataSource` is the technology-neutral core interface:

`source.snapshot(request) -> MarketSnapshot`

Every source exposes a non-empty `source_id`. The response must preserve request scope and reference time and contain only data that satisfies the downstream PIT contract.

## Ingestion

`ingest()` is the fail-closed boundary between a source and the rest of the decision pipeline. It validates the request/source boundary, verifies source identity and scope, and runs snapshot validation. No fallback, repair, trimming, inference, or lookahead is permitted.

## Production provider boundary

A real provider adapter belongs behind `MarketDataSource`. Provider-specific transport/auth/rate-limit/reconnect/pagination/timeframe behavior is implemented only after the provider's external contract is verified.

## Deterministic reference implementation

`InMemoryMarketDataSource` is for unit tests and replay fixtures. It does not simulate an exchange or generate market data.

## Safety invariants

- UTC timestamps only.
- Closed candles only: `close_time < reference_time`.
- No future data.
- No silent repair or inference.
- Immutable snapshots.
- Deterministic source identity and request scope.
- Runtime does not mutate Git or persist secrets.
- No order execution or auto-trading.

## Acceptance

Source-layer acceptance requires contract, unit, failure-path, PIT, deterministic retrieval, and provider-adapter tests followed by GREEN CI before any provider is treated as production-active.
