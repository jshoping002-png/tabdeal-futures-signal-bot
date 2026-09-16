# Information Source Data Classification V1

## Status

**DESIGNED — ORTHOGONAL TO PROJECT LIFECYCLE PHASES**

This document defines how information sources are classified by the **data they provide** and by the **system consumer that may use that data**. It does not replace the project's lifecycle phases.

## Core distinction

The project uses three separate dimensions:

1. **Lifecycle phase** — when and how work moves through the system pipeline.
2. **Data domain/class** — what kind of information a source provides.
3. **Allowed consumer** — which system layer may consume that information.

A source may therefore appear in multiple lifecycle phases while retaining one or more data-domain classifications. A lifecycle phase must not be used as a substitute for the data type.

## Lifecycle phases

The existing lifecycle remains:

1. Requirements and architecture
2. Contracts and read-only data layer
3. Real read-only adapters
4. Signal generation and validation
5. Risk and market-context evaluation
6. Notifications and output
7. Persistence, audit and replay
8. Monitoring and operational readiness

These phases describe project/system progression, not market-data taxonomy.

## Data domains

### 1. Primary Market Data

Examples: OHLCV, trades, ticker, mark/index prices, timestamps.

Typical sources: Binance Futures, Bybit Futures, Binance Spot, Bybit Spot, OKX, Kraken Futures, Coinbase Advanced Trade, Deribit.

Potential consumers: validation, series construction, strategy, risk/context, persistence and monitoring, subject to the relevant contracts.

### 2. Derivatives Market Data

Examples: open interest, funding, basis, liquidations and other verified derivatives fields.

Typical sources: public futures/derivatives interfaces where the exact field semantics are verified.

Potential consumers: intelligence, strategy only when explicitly approved by the Strategy Contract, risk/context, persistence and monitoring.

Field availability alone does not authorize strategy use.

### 3. Order Flow / Liquidity

Examples: order-book depth, spread, taker/trade-flow information and CVD-derived measures.

Potential consumers: intelligence and, only after explicit contract approval, strategy or risk.

Order-book or flow data must not enter signal logic merely because an exchange exposes the field.

### 4. Aggregated Market Context

Examples: cross-market prices, market-wide aggregates and data-quality corroboration.

Typical source: CoinMarketCap Keyless Public API.

Potential consumers: validation/corroboration, context, risk, persistence and monitoring. Strategy use requires explicit strategy authorization.

### 5. Positioning

Examples: CFTC Commitments of Traders positioning reports.

Potential consumers: contextual/risk analysis and persistence. Strategy use requires explicit strategy authorization and PIT treatment of publication timing.

### 6. Macro / Economic Data

Examples: CPI, employment, payrolls, GDP, PCE and other official economic statistics.

Typical sources: BLS, BEA, ECB, BIS, Eurostat, OECD and other official statistical agencies where access and semantics are verified.

Potential consumers: context/risk, event analysis and persistence. Direct LONG/SHORT rules are not implied.

### 7. Monetary Policy / Central-Bank Events

Examples: policy decisions, FOMC statements, official central-bank announcements and related releases.

Typical sources: Federal Reserve and other official central banks.

Potential consumers: event/context and risk, with publication-time/PIT handling.

### 8. Money Market / Rates / Liquidity

Examples: EFFR, OBFR, SOFR, Treasury yields and related money-market or financial-conditions observations.

Typical sources: Federal Reserve Bank of New York Markets Data APIs, U.S. Treasury and other officially verified sources.

Potential consumers: macro/context and risk. Strategy use requires explicit strategy authorization.

### 9. Cross-Asset Market Context

Examples: DXY, VIX, major equity indices and gold.

Potential consumers: context and risk. These sources do not become automatic LONG/SHORT conditions by registry entry alone.

### 10. News / Events

Examples: regulatory, exchange, ETF, security, geopolitical, macro and crypto-industry events.

Potential consumers: event/context and risk. Every decision-relevant item requires reliable publication/availability timing and provenance.

### 11. On-chain / Whale Activity

Examples: large transfers, exchange flows, stablecoin flows and large-address activity.

Potential consumers: intelligence/context and, only after explicit contract approval, strategy or risk.

### 12. Options / Volatility

Examples: public options metrics and volatility-surface information where a source and exact dataset are verified.

Potential consumers: derivatives intelligence, context/risk and, only after explicit strategy authorization, strategy.

## Allowed-consumer rule

Data-domain classification does not grant decision authority.

The following rule applies:

`Source -> Data Domain -> Dataset/Field -> PIT/Timing -> Validation -> Allowed Consumer -> Decision Use`

Every transition must be supported by a contract or verified project requirement. If timing, provenance, semantics, validation, or consumer authorization is missing, the data remains non-decision-eligible.

## Strategy boundary

The repository currently does not contain an approved `STRATEGY_CONTRACT_V1.md`. Therefore no source in this classification is marked as an active strategy input merely because its data is technically available.

Derivatives, order-flow, positioning, macro, cross-asset, on-chain, options, news and aggregated context remain subject to explicit strategy/risk consumption contracts.

## Point-in-Time boundary

For any data that can affect a decision, the implementation must preserve enough timing metadata to establish what was available at the decision reference time. Publication time, observation/effective time, revisions/vintages, and receipt time must not be conflated.

Ambiguous or insufficient timing is a block on decision use.

## Read-only and execution boundary

This classification introduces no order, trade, account, balance or position capability. It does not authorize private trading credentials and does not authorize automatic trading.

## Registry interpretation

The existing `Initial phase` column in `information-sources-registry.md` remains a lifecycle-phase field. The data-domain classification in this document is independent and must be used alongside it.

No source is removed, downgraded, or activated by this document.

## Acceptance

This classification is accepted as a documentation-level taxonomy only. Provider activation, adapter implementation, strategy rules, risk thresholds, or execution behavior require their own explicit contracts and verification.
