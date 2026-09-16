# Information Sources Registry

## Purpose

This document formally defines the planned information sources for the signal-analysis system. All external market-data access must remain **read-only**. No source may be used for order execution, trading, account management, balance retrieval, or position management.

## Source registry

| Source name | Domain | Planned role | Initial phase | Status |
|---|---|---|---:|---|
| Binance Futures Market Data | Crypto market data | OHLCV, volume, prices, timestamps; optional open interest, funding, liquidations and order-book data only after contract approval | 3 | planned |
| Bybit Futures Market Data | Crypto market data | OHLCV, volume, prices, timestamps; optional open interest, funding, liquidations and order-book data only after contract approval | 3 | planned |
| Binance Spot Market Data | Crypto market data | Spot reference data when a strategy or validation contract explicitly requires it | 3 | planned |
| Bybit Spot Market Data | Crypto market data | Spot reference data when a strategy or validation contract explicitly requires it | 3 | planned |
| OKX Market Data | Crypto market data | Independent exchange market-data corroboration; exact fields only after provider contract approval | 3 | planned |
| Kraken Futures Market Data | Crypto futures market data | Independent futures candles and public derivatives/analytics context; exact fields only after provider contract approval | 3 | planned |
| Coinbase Advanced Trade Market Data | Crypto market data | Independent spot market-data corroboration; derivatives use not assumed | 3 | planned |
| Deribit Market Data | Crypto derivatives/market data | Independent futures/options/spot market-data corroboration; exact fields only after provider contract approval | 3 | planned |
| Other approved public exchange market-data sources | Crypto market data | Redundancy, comparison and data-quality cross-checks | 3 | planned |
| CFTC Commitments of Traders (COT) | Futures positioning | Weekly positioning context and independent positioning cross-check; PIT publication timing required | 2 | planned |
| CoinMarketCap Keyless Public API | Aggregated crypto market context | Cross-market corroboration and anomaly/data-quality cross-checks; not primary high-frequency feed | 2 | planned |
| TradingView | Aggregated market context / validation | Observation or independent data source only after its exact role, licensing and access contract are approved | 2 | role pending |
| Federal Reserve | Macroeconomic data | Interest-rate decisions, FOMC statements, policy announcements and related official releases | 2 | planned |
| Bureau of Labor Statistics (BLS) | Macroeconomic data | CPI, NFP, payrolls, unemployment and other employment statistics | 2 | planned |
| Bureau of Economic Analysis (BEA) | Macroeconomic data | PCE, GDP and related national-account statistics | 2 | planned |
| European Central Bank (ECB) Data Portal API | Macroeconomic/financial data | Independent official euro-area rates, exchange rates and macro/financial context; exact series only after provider contract approval | 2 | planned |
| Official central banks and statistical agencies outside the US | Macroeconomic data | Country-specific rates, inflation, employment, GDP, PMI and official releases | 2 | planned |
| Approved financial-news sources | News and risk events | Macro news, central-bank actions, financial crises, geopolitics, ETFs, regulation, crypto-industry and exchange/institution news | 2 | source shortlist pending |
| DXY | Macro/market context | Dollar-strength context; never an automatic LONG/SHORT condition by itself | 2 | planned |
| VIX | Macro/market context | Volatility-risk context; never an automatic LONG/SHORT condition by itself | 2 | planned |
| US Treasury yields | Macro/market context | Rates and liquidity context; exact maturities must be specified before implementation | 2 | planned |
| Major equity indices | Macro/market context | Cross-asset risk context; exact indices must be specified before implementation | 2 | planned |
| Gold | Macro/market context | Cross-asset risk context; never an automatic LONG/SHORT condition by itself | 2 | planned |
| Liquidity / financial-conditions indicators | Macro/market context | Broader liquidity and financial-conditions context; exact provider and series must be specified | 2 | provider pending |

## Distribution by project phase

| Phase | Sources assigned to the phase |
|---|---|
| **1 — Requirements and architecture** | Binance Futures Market Data; Bybit Futures Market Data; Binance Spot Market Data; Bybit Spot Market Data; OKX; Kraken Futures; Coinbase Advanced Trade; Deribit; CFTC COT; CoinMarketCap Keyless Public API; TradingView; Federal Reserve; BLS; BEA; ECB Data Portal API; official non-US central banks/statistical agencies; approved financial-news sources; DXY; VIX; US Treasury yields; major equity indices; Gold; Liquidity/financial-conditions indicators |
| **2 — Contracts and read-only data layer** | CFTC COT; CoinMarketCap Keyless Public API; ECB Data Portal API; TradingView role definition; Federal Reserve; BLS; BEA; official non-US macro sources; approved financial-news sources; DXY; VIX; US Treasury yields; major equity indices; Gold; Liquidity/financial-conditions indicators; source metadata and provenance contracts |
| **3 — Real read-only adapters** | Binance Futures Market Data; Bybit Futures Market Data; Binance Spot Market Data when approved; Bybit Spot Market Data when approved; OKX; Kraken Futures; Coinbase Advanced Trade; Deribit; other approved public exchange market-data sources; TradingView only if its source/adapter contract is approved |
| **4 — Signal generation and validation** | Normalized data from approved exchange sources; COT positioning context; CoinMarketCap aggregated corroboration; ECB macro/financial context; OHLCV/volume/price/timestamp data; optional open interest, funding, liquidations and order-book data only if explicitly included in the Strategy Contract; approved macro/news context from phase 2 |
| **5 — Risk and market-context evaluation** | CFTC COT; CoinMarketCap aggregated market context; ECB macro/financial context; Federal Reserve; BLS; BEA; official macro sources; approved news sources; DXY; VIX; US Treasury yields; major equity indices; Gold; liquidity/financial-conditions indicators; normalized exchange data |
| **6 — Notifications and output** | Signal results, validation results, risk warnings, source/provenance metadata, Telegram Bot and Outbox as output infrastructure—not market-data sources |
| **7 — Persistence, audit and replay** | Snapshots and provenance from Binance/Bybit/other approved read-only sources; CFTC COT reports used in decisions; CoinMarketCap data used in decisions; ECB data used in decisions; TradingView data if approved; macro releases; news/events used in decisions; context indicators; decision and rule-version records |
| **8 — Monitoring and operational readiness** | Health, freshness, latency and error metrics for every implemented source; API availability; macro/news ingestion health; context-series freshness; CI, runtime logs, audit and replay evidence |

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

This registry records the planned source architecture. It does **not** claim that live adapters are implemented or that external source access has been verified for production. The current repository contains read-only contracts and a static data source; real external adapters remain planned work.

**Production readiness = NOT VERIFIED**
