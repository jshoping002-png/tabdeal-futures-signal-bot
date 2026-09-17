# Information Sources Registry

## Purpose

This document formally defines the planned information sources for the signal-analysis system. All external market-data access must remain **read-only**. No source may be used for order execution, trading, account management, balance retrieval, or position management.

## Source registry

The following initial-batch sources were removed from the operational source list because their use requires live external data access, which is outside the currently available verification path. Their historical verification reports remain preserved in `docs/information-source-verification-batch-001.md` through `docs/information-source-verification-batch-006.md`.

| Source name | Domain | Planned role | Initial phase | Status |
|---|---|---|---:|---|
| Other approved public exchange market-data sources | Crypto market data | Redundancy, comparison and data-quality cross-checks | 3 | planned |
| TradingView | Aggregated market context / validation | Observation or independent data source only after its exact role, licensing and access contract are approved | 2 | role pending |
| Federal Reserve | Macroeconomic data | Interest-rate decisions, FOMC statements, policy announcements and related official releases | 2 | planned |
| Federal Reserve Bank of New York Markets Data APIs | U.S. money-market / liquidity context | Independent reference-rate and money-market context including EFFR, OBFR, SOFR, TGCR/BGCR and related public market data; exact routes only after provider contract approval | 2 | planned |
| Bureau of Economic Analysis (BEA) | Macroeconomic data | PCE, GDP and related national-account statistics | 2 | planned |
| OECD Data Explorer SDMX API | International macroeconomic/financial data | Independent cross-country macro/financial context and corroboration; exact series only after provider contract approval | 2 | planned |
| Official central banks and statistical agencies outside the US | Macroeconomic data | Country-specific rates, inflation, employment, GDP, PMI and official releases | 2 | planned |
| Approved financial-news sources | News and risk events | Macro news, central-bank actions, financial crises, geopolitics, ETFs, regulation, crypto-industry and exchange/institution news | 2 | source shortlist pending |
| DXY | Macro/market context | Dollar-strength context; never an automatic LONG/SHORT condition by itself | 2 | planned |
| VIX | Macro/market context | Volatility-risk context; never an automatic LONG/SHORT condition by itself | 2 | planned |
| US Treasury yields | Macro/market context | Rates and liquidity context; exact maturities must be specified before implementation | 2 | planned |
| Major equity indices | Macro/market context | Cross-asset risk context; exact indices must be specified before implementation | 2 | planned |
| Gold | Macro/market context | Cross-asset risk context; never an automatic LONG/SHORT condition by itself | 2 | planned |
| Liquidity / financial-conditions indicators | Macro/market context | Broader liquidity and financial-conditions context; exact provider and series must be specified | 2 | provider pending |

## Initial-batch live-call exclusions

The following 16 source entries from verification batches 001–006 are intentionally absent from the operational registry above:

- Binance Futures Market Data
- Bybit Futures Market Data
- Binance Spot Market Data
- Bybit Spot Market Data
- OKX Market Data
- Kraken Futures Market Data
- Coinbase Advanced Trade Market Data
- Deribit Market Data
- CFTC Commitments of Traders (COT)
- CoinMarketCap Keyless Public API
- Bureau of Labor Statistics (BLS)
- U.S. Treasury Daily Interest-Rate Data
- SEC EDGAR Public APIs
- European Central Bank Data Portal API
- Bank for International Settlements (BIS) Statistics API
- Eurostat REST / SDMX APIs

This is an operational source-list removal only. It does not rewrite or delete the historical verification reports.

## Distribution by project phase

| Phase | Sources assigned to the phase |
|---|---|
| **1 — Requirements and architecture** | Other approved public exchange market-data sources; TradingView; Federal Reserve; Federal Reserve Bank of New York Markets Data APIs; BEA; OECD Data Explorer SDMX API; official non-US central banks/statistical agencies; approved financial-news sources; DXY; VIX; US Treasury yields; major equity indices; Gold; Liquidity/financial-conditions indicators |
| **2 — Contracts and read-only data layer** | TradingView role definition; Federal Reserve; Federal Reserve Bank of New York Markets Data APIs; BEA; OECD Data Explorer SDMX API; official non-US macro sources; approved financial-news sources; DXY; VIX; US Treasury yields; major equity indices; Gold; Liquidity/financial-conditions indicators; source metadata and provenance contracts |
| **3 — Real read-only adapters** | Other approved public exchange market-data sources; TradingView only if its source/adapter contract is approved |
| **4 — Signal generation and validation** | Normalized data from approved exchange sources; OECD macro/financial context; OHLCV/volume/price/timestamp data; optional open interest, funding, liquidations and order-book data only if explicitly included in the Strategy Contract; approved macro/news context from phase 2 |
| **5 — Risk and market-context evaluation** | OECD macro/financial context; Federal Reserve; Federal Reserve Bank of New York Markets Data APIs; BEA; official macro sources; approved news sources; DXY; VIX; US Treasury yields; major equity indices; Gold; liquidity/financial-conditions indicators; normalized exchange data |
| **6 — Notifications and output** | Signal results, validation results, risk warnings, source/provenance metadata, Telegram Bot and Outbox as output infrastructure—not market-data sources |
| **7 — Persistence, audit and replay** | Snapshots and provenance from approved read-only sources; OECD data used in decisions; macro releases; news/events used in decisions; context indicators; decision and rule-version records |
| **8 — Monitoring and operational readiness** | Health, freshness, latency and error metrics for every implemented source; API availability; macro/news ingestion health; context-series freshness; CI, runtime logs, audit and replay evidence |

## Data-domain classification

Lifecycle phase and data type are intentionally separate dimensions. The `Initial phase` column above describes **project/system lifecycle placement**; it does not classify the kind of data supplied by a source.

The authoritative data-domain taxonomy is defined in `docs/information-source-data-classification-v1.md` and uses the following classes:

1. Primary Market Data
2. Derivatives Market Data
3. Order Flow / Liquidity
4. Aggregated Market Context
5. Positioning
6. Macro / Economic Data
7. Monetary Policy / Central-Bank Events
8. Money Market / Rates / Liquidity
9. Cross-Asset Market Context
10. News / Events
11. On-chain / Whale Activity
12. Options / Volatility

A source can therefore participate in multiple lifecycle phases without changing its data-domain classification. Dataset/field-level authorization remains separate from source registration.

For the current source-by-source mapping, including dataset/field scope, allowed consumer and PIT/decision status, see `docs/source-data-domain-mapping-v1.md`.

## Allowed-consumer rule

Data-domain classification does not grant decision authority. Decision use follows:

`Source → Data Domain → Dataset/Field → PIT/Timing → Validation → Allowed Consumer → Decision Use`

Missing or ambiguous timing, provenance, semantics, validation, or consumer authorization blocks decision use. In particular, the existence of derivatives, order-book, positioning, macro, news, on-chain, options, or aggregated fields does not by itself authorize LONG/SHORT strategy use.

The repository currently has no approved `STRATEGY_CONTRACT_V1.md`; therefore this classification does not mark any newly classified external source as an active strategy input.

## Required source-level controls

Every implemented source must define:

- read-only access boundary;
- exact endpoint or dataset allowlist;
- authentication requirements, if any, without private trading/account capabilities;
- schema and normalization rules;
- `available_at`, `received_at` and timezone semantics;
- provenance and source version metadata;
- Point-in-Time and no-look-ahead behavior;
- freshness, completeness and validity checks;
- timeout, retry and failure behavior;
- fallback and quarantine behavior;
- audit and replay requirements;
- explicit prohibition of order, trade, balance, position and account endpoints.

## Important status note

This registry records the current operational source architecture. The 16 initial-batch sources listed in the exclusion section are no longer part of the operational source list because they depend on live external data access. Their historical verification reports are preserved for audit/history. Remaining sources are still planned/role-pending and are not production-active.

**Operational source-list removals:** 16  
**Providers activated:** 0  
**Strategy rules added:** 0  
**Execution capability added:** 0  
**Production readiness = NOT VERIFIED**
