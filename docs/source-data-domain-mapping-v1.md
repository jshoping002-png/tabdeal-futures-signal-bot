# Source Data Domain Mapping V1

## Status

**DESIGNED — DOCUMENTATION-LEVEL MAPPING; NO PROVIDER ACTIVATION**

This document maps the sources currently present in `information-sources-registry.md` to the data domain, documented dataset/field scope, access status, PIT/timing status, allowed consumer, and production status supported by the repository contracts. Initial-batch sources removed from the operational registry because they require live external data access are preserved only in the historical verification reports.

This is a source-to-data mapping. It does not create strategy rules, activate providers, or authorize execution.

## Interpretation rules

The mapping follows:

`Source -> Data Domain -> Dataset/Field -> Access -> PIT/Timing -> Validation -> Allowed Consumer -> Production Status`

- `verified` means the repository's source-verification work recorded evidence for that point.
- `candidate` means the source is registered/planned but provider-level production activation is not complete.
- `pending` means the repository does not contain sufficient evidence to define the item precisely.
- `blocked` means decision use is not permitted until the missing contract/evidence exists.
- The repository has no approved `STRATEGY_CONTRACT_V1.md`; therefore no row is an active strategy input.

## Source-by-source mapping

| Source | Data Domain | Dataset / Field Scope supported by current docs | Access Status | PIT / Timing Status | Allowed Consumer now | Production Status |
|---|---|---|---|---|---|---|
| Other approved public exchange market-data sources | Primary Market Data / provider-specific derivatives domains | Only fields explicitly approved for a specific provider | Must be verified per provider | Must be verified per provider | Validation/corroboration and context after provider approval; strategy blocked | Planned |
| TradingView | Aggregated Market Context | Observation/reference use only; programmatic dataset not defined | Public charts do not establish a production API contract | Pending separate source contract and licensing/access verification | Reference/observation only; no decision use until contract | Role pending |
| Federal Reserve | Monetary Policy / Central-Bank Events; Macro / Economic Data | Interest-rate decisions, FOMC statements, policy announcements and official releases | Public official information | Publication-time/PIT handling required | Event/context and risk, persistence/audit | Planned |
| Federal Reserve Bank of New York Markets Data APIs | Money Market / Rates / Liquidity | EFFR, OBFR, SOFR, TGCR/BGCR, SOFR averages/index and related public market data | Public API path recorded; authentication is not fully verified for every route | Publication/effective timing and revisions must be contracted per selected route | Macro/context, risk, persistence/monitoring; strategy blocked | Planned |
| Bureau of Economic Analysis (BEA) | Macro / Economic Data | PCE, GDP and related national-account statistics | Public/no-key candidate; exact access path/series not fully verified in current contracts | Publication/revision semantics pending | Context/risk and persistence after verification | Planned |
| OECD Data Explorer SDMX API | Macro / Economic Data | Cross-country macro/financial datasets; exact series require selection | Public/free API path recorded; rate limiting applies | Publication/revision timing and dataset versioning required | Context/risk, corroboration, persistence/audit; strategy blocked | Candidate |
| Official central banks and statistical agencies outside the US | Macro / Economic Data; Monetary Policy / Central-Bank Events | Country-specific rates, inflation, employment, GDP, PMI and official releases | Must be verified per institution/source | Must be verified per series/release | Context/risk and event analysis after source verification | Planned |
| Approved financial-news sources | News / Events | Regulatory, exchange, ETF, security, geopolitical, crypto-industry and macro events | Source shortlist pending; public/unauthenticated access required | Publication/availability timestamp and provenance mandatory | Event/context and risk after source approval; strategy blocked | Source shortlist pending |
| DXY | Cross-Asset Market Context | Dollar-strength market context; exact provider/index feed pending | Provider not specified in current registry contract | Timing/provider semantics pending | Context/risk only; not an automatic LONG/SHORT condition | Planned |
| VIX | Cross-Asset Market Context; Options / Volatility | Volatility-risk context; exact provider/index feed pending | Provider not specified in current registry contract | Timing/provider semantics pending | Context/risk only; not an automatic LONG/SHORT condition | Planned |
| US Treasury yields | Money Market / Rates / Liquidity; Cross-Asset Market Context | Treasury yield observations; exact maturities must be specified | Public official source candidate; exact series selection pending | Publication/effective timing and revision semantics required | Macro/context and risk after exact series contract | Planned |
| Major equity indices | Cross-Asset Market Context | Cross-asset equity-index context; exact indices/provider pending | Provider not specified in current registry contract | Timing/provider semantics pending | Context/risk after exact provider/series contract | Planned |
| Gold | Cross-Asset Market Context | Cross-asset gold context; exact provider/feed pending | Provider not specified in current registry contract | Timing/provider semantics pending | Context/risk only; not an automatic LONG/SHORT condition | Planned |
| Liquidity / financial-conditions indicators | Money Market / Rates / Liquidity | Broader liquidity/financial-conditions indicators; provider and series not specified | Provider pending | Timing/revision semantics pending | Context/risk after provider and series verification | Provider pending |

## Initial-batch live-call exclusions

The following 16 sources from verification batches 001–006 are intentionally excluded from the operational mapping because their use requires live external data access:

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

The historical verification reports remain unchanged and are not themselves part of the operational source registry.

## Strategy authorization

The repository currently does not contain an approved `STRATEGY_CONTRACT_V1.md`. Consequently:

- no source above is an active strategy input;
- no derivative, order-flow, positioning, macro, cross-asset, on-chain, options, news, or aggregated field is converted into a LONG/SHORT rule;
- field availability does not imply strategy authority.

## PIT authorization

A source can be technically public and still be blocked for decision use if its availability time, publication time, observation/effective time, revision/vintage behavior, or receipt time is insufficient for the decision boundary. The project requires strict point-in-time handling and closed-candle semantics.

## Execution boundary

This mapping adds no order, trade, account, balance, position, private trading credential, or automatic-trading capability. The source contracts explicitly separate external intelligence from strategy and execution.

## Validation checklist

For each source remaining in the operational registry, before production activation:

1. Verify exact endpoint/dataset allowlist.
2. Verify public/no-key access for the required path.
3. Verify schema and field semantics.
4. Verify `available_at`, publication/effective time, receipt time, timezone and revision/vintage behavior as applicable.
5. Verify PIT/no-look-ahead behavior.
6. Verify freshness, completeness and invalid-data handling.
7. Verify timeout/retry/failure/quarantine behavior.
8. Verify provenance and replay metadata.
9. Verify the allowed consumer through an explicit domain/strategy/risk contract.
10. Require implementation and GREEN CI evidence before production activation.

## Acceptance

This document is a documentation-level source-to-data mapping only.

**Produced:** 1 mapping document  
**Corrected:** 1 existing document replaced before this exclusion update  
**Sources removed from operational mapping:** 16  
**Historical verification reports deleted:** 0  
**Providers activated:** 0  
**Strategy rules added:** 0  
**Execution behavior added:** 0  
**Production readiness:** NOT VERIFIED
