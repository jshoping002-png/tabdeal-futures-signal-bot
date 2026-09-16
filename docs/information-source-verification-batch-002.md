# Information Source Verification Batch 002

## Batch status

`FINAL — VALIDATED BEFORE COMMIT`

This batch records only evidence verified against official provider documentation and the repository source contracts. It does not activate any provider, add strategy rules, remove any source, or add trading/execution capability.

## Record 001 — Binance Spot Market Data

- **Source:** Binance Spot API official documentation.
- **Domain:** Crypto spot market data.
- **Verified public-data boundary:** Binance documents `NONE` as the security type for public market data and directs public market-data use to `https://data-api.binance.vision`.
- **Verified transport semantics:** The Spot REST documentation states JSON responses by default, millisecond timestamps by default, chronological ordering unless an endpoint specifies otherwise, and documented request-weight/rate-limit controls.
- **Endpoint verification status:** The current official documentation portal confirms Spot REST market-data coverage, but the exact current public kline endpoint page was not independently retrievable in this review. Therefore this record does not overclaim a specific kline path beyond the documented public market-data boundary.
- **Project eligibility:** `CANDIDATE — PUBLIC MARKET-DATA SECURITY TYPE VERIFIED`.
- **Production status:** `NOT ACTIVE`.
- **Reason:** Before production activation, the exact selected endpoint set, response schema, rate limits, timestamp/availability semantics, historical pagination and failure behavior must be verified and contracted.
- **Strategy use:** No strategy consumption is approved.
- **Execution boundary:** No order, account, balance, position, or execution endpoint is approved.
- **Official reference:** https://developers.binance.com/en/docs/products/spot/rest-api

## Record 002 — Bybit Spot Market Data

- **Source:** Bybit V5 official market-data documentation.
- **Domain:** Crypto spot market data.
- **Verified kline coverage:** `GET /v5/market/kline` explicitly covers Spot as well as derivatives products; it accepts `start`/`end` timestamps and a page limit of 1–1000, and returns candle timing and OHLCV-related fields.
- **Verified ticker coverage:** `GET /v5/market/tickers` explicitly supports `category=spot` and returns spot bid/ask, last price, 24-hour high/low, volume and turnover fields.
- **Verified public WebSocket boundary:** Bybit documents a public Spot WebSocket endpoint and states that public topics do not require authentication.
- **Operational restriction:** Bybit documents geographic restrictions for some source IP locations; this must be treated as provider availability behavior rather than silently bypassed.
- **Project eligibility:** `CANDIDATE — PUBLIC SPOT PATH VERIFIED`.
- **Production status:** `NOT ACTIVE`.
- **Reason:** Exact endpoint allowlist, REST/WS rate limits, timestamp/availability semantics, reconnect behavior and project-specific PIT handling still require a provider contract.
- **Strategy use:** No strategy consumption is approved.
- **Execution boundary:** No order, account, balance, position, or execution endpoint is approved.
- **Official references:** https://bybit-exchange.github.io/docs/v5/market/kline ; https://bybit-exchange.github.io/docs/v5/market/tickers ; https://bybit-exchange.github.io/docs/v5/ws/connect

## Record 003 — U.S. Treasury Daily Interest-Rate Data

- **Source:** U.S. Department of the Treasury official Daily Interest Rate XML feed.
- **Domain:** Macro / rates context.
- **Verified interface:** Treasury documents a GET-based XML feed at the official Treasury host and provides endpoint parameters for daily Treasury yield-curve, bill-rate, long-term-rate and real-yield datasets.
- **Verified history:** Treasury documents availability from 1990 for Daily Treasury Par Yield Curve Rates, with other rate families beginning in later years; an `all` feed with pagination is documented for historical retrieval.
- **Verified pagination:** Treasury documents zero-based pagination for the `all` feed and instructs clients to continue until no `<entry>` data remains.
- **Current data visibility:** Treasury's current daily-rates pages expose daily par-yield data and multiple maturities, including 1-month through 30-year tenors where available.
- **Authentication evidence:** The reviewed feed documentation specifies direct GET access but does not state a required API key or account credential. This batch therefore records the path as public-access evidence, not as a broader guarantee about every Treasury data service.
- **Project eligibility:** `CANDIDATE — PUBLIC FEED PATH VERIFIED`.
- **Production status:** `NOT ACTIVE`.
- **Reason:** Exact maturity set, publication/availability timestamp semantics, revision policy and PIT treatment must be contracted before the data can affect decisions.
- **Strategy use:** No automatic LONG/SHORT condition is approved.
- **Official references:** https://home.treasury.gov/treasury-daily-interest-rate-xml-feed ; https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics/interest-rate-xml-files

## Record 004 — SEC EDGAR Public APIs

- **Source:** U.S. Securities and Exchange Commission official EDGAR APIs.
- **Domain:** Regulatory filings / event-risk context.
- **Verified access:** SEC states that `data.sec.gov` provides REST APIs delivering JSON-formatted data and that these APIs do not require authentication or API keys.
- **Verified data classes:** SEC documents submissions history by filer and extracted XBRL data for filings including 10-K, 10-Q, 8-K and other listed forms.
- **Project role:** Regulatory/event context only; this source does not become a trading rule by virtue of being available.
- **Operational controls:** SEC access must still comply with the SEC's published fair-access and request-rate guidance when an adapter is designed.
- **Project eligibility:** `CANDIDATE — NO-KEY PATH VERIFIED`.
- **Production status:** `NOT ACTIVE`.
- **Reason:** The exact filing/event datasets, availability timestamps, retrieval freshness, historical/revision semantics and PIT treatment must be contracted before decision influence.
- **Strategy use:** No direct LONG/SHORT rule is approved.
- **Execution boundary:** No order, account, balance, position, or execution endpoint is approved.
- **Official reference:** https://www.sec.gov/search-filings/edgar-application-programming-interfaces

## Batch validation result

The four records were validated together before commit against the repository source registry/contracts and the official provider documentation cited in each record.

- **Records produced:** 4
- **Records requiring correction during validation:** 0
- **Records finally approved for this batch:** 4
- **Source-list removals:** 0
- **Provider activations:** 0
- **Strategy rules added:** 0
- **Order/execution capabilities added:** 0
- **Unsupported items left explicitly unresolved:** exact Binance Spot kline endpoint page/schema in the current documentation portal; provider-specific rate limits and PIT/revision semantics for all four sources; exact Treasury maturity set for project use; exact SEC event dataset and availability semantics.

## Repository contracts used for validation

- `docs/MARKET_INFORMATION_SOURCES_CONTRACT_V1.md`
- `docs/DATA_SOURCE_CONTRACT_V1.md`
- `docs/PHASE_1_2_SOURCE_BOUNDARY.md`
- `docs/information-sources-registry.md`
- `docs/information-source-verification-batch-001.md`
