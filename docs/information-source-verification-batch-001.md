# Information Source Verification Batch 001

## Batch status

`FINAL — VALIDATED BEFORE COMMIT`

This batch records only evidence verified against official provider documentation and the repository contracts. It does not activate any provider, add a strategy rule, or remove any existing source from the registry.

## Record 001 — Binance Futures Market Data

- **Source:** Binance Futures public market-data documentation.
- **Domain:** Crypto derivatives market data.
- **Verified data paths:** The official Futures market-data documentation exposes public market-data sections for continuous-contract klines, index/mark price, funding, open interest, order book, trades, taker buy/sell volume and related market data.
- **Verified kline semantics:** The continuous-contract kline endpoint is `GET /dapi/v1/continuousKlines`; it accepts contract type and interval, returns open/close times and OHLCV-related fields, supports a maximum `limit` of 1500, and documents a maximum 200-day start/end span.
- **Rate-limit evidence:** The documentation states that these market-data endpoints consume IP-based request weight and publishes endpoint-specific weights/limits.
- **Authentication evidence:** The reviewed official market-data documentation is sufficient to establish the public market-data endpoint surface, but this batch does not claim that every Binance endpoint potentially needed by the project has identical authentication semantics.
- **Project eligibility:** `VERIFICATION_INCOMPLETE`.
- **Production status:** `NOT ACTIVE`.
- **Reason:** Before production activation, the project still requires a provider-specific contract covering the exact selected endpoints, no-key access for those exact endpoints, rate limits, timestamps/availability, history, pagination/reconnect behavior, symbol/timeframe semantics and failure behavior.
- **Strategy use:** No strategy consumption is approved by this record.
- **Execution boundary:** No order, account, balance, position, or execution endpoint is approved.
- **Official reference:** https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-coin-m-futures/api/rest-api/market-data

## Record 002 — Bybit Futures Market Data

- **Source:** Bybit V5 public market-data documentation.
- **Domain:** Crypto derivatives market data.
- **Verified kline data:** `GET /v5/market/kline` covers Spot, USDT, USDC and Inverse products; it accepts `start`/`end` timestamps and a page limit from 1 to 1000. The response includes candle start time and OHLCV-related fields and is returned in reverse start-time order.
- **Verified open-interest data:** `GET /v5/market/open-interest` covers USDT, USDC and Inverse contracts; it supports start/end timestamps, a page limit from 1 to 200, cursor pagination, and returns a timestamp with the open-interest value.
- **Freshness/latency evidence:** Bybit explicitly warns that extreme market volatility can cause increased latency or temporary delays in open-interest data delivery.
- **Authentication evidence:** The reviewed official market-data pages document the public market-data endpoint surface, but this batch does not claim that every Bybit endpoint potentially needed by the project has identical authentication semantics.
- **Project eligibility:** `VERIFICATION_INCOMPLETE`.
- **Production status:** `NOT ACTIVE`.
- **Reason:** Before production activation, the project still requires a provider-specific contract covering the exact selected endpoints, no-key access for those exact endpoints, rate limits, timestamps/availability, history, pagination/reconnect behavior, symbol/timeframe semantics and failure behavior.
- **Strategy use:** No strategy consumption is approved by this record.
- **Execution boundary:** No order, account, balance, position, or execution endpoint is approved.
- **Official references:** https://bybit-exchange.github.io/docs/v5/market/kline ; https://bybit-exchange.github.io/docs/v5/market/open-interest

## Record 003 — U.S. Bureau of Labor Statistics Public Data API

- **Source:** U.S. Bureau of Labor Statistics (BLS) Public Data API.
- **Domain:** Official macroeconomic/labor statistics.
- **Verified no-key access:** BLS states that Version 1.0 is an unregistered API and does not require registration. Version 2.0 requires registration and provides higher limits.
- **Verified limits:** BLS documents for Version 1.0 a daily limit of 25 queries, up to 25 series per query, and up to 10 years per query. The documented request-rate limit is 50 requests per 10 seconds for both versions.
- **Verified interface:** BLS documents REST access through GET and POST and provides JSON examples for Version 1.0.
- **Verified historical-data limitation:** BLS states that Version 1.0 returns observational values and footnotes and does not include metadata. BLS also documents a one-day lag between published data and API availability in its API feature notes.
- **Project eligibility:** `CANDIDATE — NO-KEY PATH VERIFIED`.
- **Production status:** `NOT ACTIVE`.
- **Reason:** Exact series identifiers, publication/availability semantics, revision behavior and the project's PIT treatment still need to be contracted before BLS data can affect decisions.
- **Strategy use:** No direct LONG/SHORT rule is approved. Macro data remains context/risk input until a separate decision-consumption contract exists.
- **Official references:** https://www.bls.gov/developers/ ; https://www.bls.gov/developers/api_FAQs.htm ; https://www.bls.gov/bls/api_features.htm ; https://www.bls.gov/developers/api_signature.htm

## Record 004 — Strategy Contract V1 Documentation Gap

- **Finding:** The current `main` tree does not contain `docs/STRATEGY_CONTRACT_V1.md`.
- **Verified repository boundary:** The repository source/data contracts require separate strategy-consumption contracts before external intelligence can influence Strategy or Risk Gate.
- **Impact:** Strategy thresholds, feature-to-decision mappings, indicator windows, multi-timeframe rules, and allowed use of derivatives/order-flow/context data must not be invented or inferred from the source inventory.
- **Project status:** `BLOCKED FOR STRATEGY-SPECIFIC IMPLEMENTATION`.
- **Required evidence:** A documented Strategy Contract defining approved inputs, required data, timeframes, decision semantics, LONG/SHORT isolation, conflict behavior, and versioning.
- **Safety boundary:** No new strategy rule and no automatic trade behavior is introduced by this batch.

## Batch validation result

The four records were validated together before commit against the current repository source contracts and the official provider documentation listed above.

- **Records produced:** 4
- **Records requiring correction during validation:** 1 (the initial wording of the Binance/Bybit authentication evidence was narrowed so it did not overclaim endpoint-wide authentication semantics).
- **Records finally approved for this batch:** 4
- **Source-list removals:** 0
- **Provider activations:** 0
- **Strategy rules added:** 0
- **Order/execution capabilities added:** 0
- **Unsupported items left explicitly unresolved:** exact provider endpoint authentication for every selected Binance/Bybit path; exact macro series/PIT semantics; Strategy Contract V1.

## Repository contracts used for validation

- `docs/MARKET_INFORMATION_SOURCES_CONTRACT_V1.md`
- `docs/DATA_SOURCE_CONTRACT_V1.md`
- `docs/PHASE_1_2_SOURCE_BOUNDARY.md`
- `docs/information-sources-registry.md`
- `README.md`
