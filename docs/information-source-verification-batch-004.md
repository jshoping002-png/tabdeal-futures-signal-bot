# Information Source Verification Batch 004

## Batch status

`FINAL — VALIDATED BEFORE COMMIT`

This batch adds only sources whose official documentation verifies a public/free API path compatible with the project source policy. No source is removed, no provider is activated, no strategy rule is added, and no trading/execution capability is added.

## Record 001 — CFTC Commitments of Traders (COT)

- **Source:** U.S. Commodity Futures Trading Commission (CFTC) Public Reporting Environment.
- **Domain:** Futures positioning / market context.
- **Verified public API boundary:** CFTC states that it is not currently providing API tokens for the Public Reporting APIs and that users are generally able to use the API without a token as long as the API is not overused. The Public Reporting Environment provides API access to query/filter COT datasets.
- **Verified data boundary:** COT includes weekly reports; the CFTC user guide states reports are published weekly on Fridays with data as of the prior Tuesday's close. The Public Reporting Environment supports query/download and formats including CSV, XML, RSS, RDF and TSV.
- **Project value:** Independent positioning context can complement exchange market data and help identify positioning changes or disagreement with price/derivatives observations.
- **Critical PIT limitation:** Because the report is weekly and publication occurs after the report's observation date, report availability time must be modeled explicitly. COT data must not be treated as intraday information available at the underlying Tuesday close.
- **Project eligibility:** `CANDIDATE — PUBLIC NO-TOKEN API VERIFIED`.
- **Production status:** `NOT ACTIVE`.
- **Reason:** Exact contract market/dataset selection, publication timestamp, historical retrieval semantics, revision behavior and PIT snapshot rules require a provider-specific contract before decision use.
- **Strategy use:** Positioning is contextual evidence only. It is not by itself a LONG/SHORT rule and cannot override the Strategy Contract.
- **Execution boundary:** No trading, account, order or execution endpoint is required or approved.
- **Official references:** https://www.cftc.gov/es/node/128971 ; https://publicreporting.cftc.gov/stories/s/Public-Reporting-FAQ/inwp-fmhz/ ; https://publicreporting.cftc.gov/stories/s/COT-Help/p2fg-u73y/

## Record 002 — CoinMarketCap Keyless Public API

- **Source:** CoinMarketCap official API documentation.
- **Domain:** Aggregated crypto market data / cross-market confirmation.
- **Verified public API boundary:** CoinMarketCap documents a Keyless Public API using `https://pro-api.coinmarketcap.com/public-api` with no API key, no signup and no authentication header for supported endpoints.
- **Verified data boundary:** Official documentation states the keyless API provides a curated subset of endpoints including live crypto market data and historical data; the exact keyless endpoint subset is provider-controlled and can change. The official FAQ states the keyless path exposes 35+ live production endpoints and is rate-limited.
- **Project value:** Aggregated cross-exchange information can provide an additional market-data view for corroboration and anomaly detection alongside the project's direct exchange sources.
- **Critical limitation:** The keyless path is rate-limited and has a curated endpoint subset. It must not be treated as the project's primary high-frequency market feed. Endpoint coverage and historical/PIT semantics must be verified for every exact dataset selected.
- **Project eligibility:** `CANDIDATE — PUBLIC KEYLESS API VERIFIED`.
- **Production status:** `NOT ACTIVE`.
- **Reason:** Exact selected endpoints, response schema, rate behavior under project polling, historical coverage, timestamp/availability semantics and PIT handling require a provider-specific contract before decision use.
- **Strategy use:** Aggregated data is corroboration/context only unless explicitly admitted by the Strategy Contract. No automatic LONG/SHORT rule is created by adding this source.
- **Execution boundary:** Only public market-data endpoints are in scope. No account, private, order or execution endpoint is approved.
- **Official references:** https://coinmarketcap.com/api/documentation/pro-api-reference/keyless-public-api ; https://coinmarketcap.com/api/faq/ ; https://coinmarketcap.com/api/pricing/

## Explicitly not added in this batch

- **CoinGecko:** Official documentation currently presents a keyless public API for light experimentation/prototyping, while other official support documentation states that API access requires an API key. Because the official documentation set is internally inconsistent for the project's production eligibility requirement, CoinGecko is not added until that ambiguity is resolved.
- **DeFiLlama:** Official API documentation confirms a Pro API and does not, in the reviewed documentation, establish the required free/no-key production API boundary clearly enough. It is not added until the exact public endpoint and access terms are verified.

## Batch validation result

- **Records produced:** 2
- **Records requiring correction during validation:** 0
- **Records finally approved for source-list addition:** 2
- **Source-list removals:** 0
- **Provider activations:** 0
- **Strategy rules added:** 0
- **Order/execution capabilities added:** 0
- **Sources explicitly deferred due to insufficient/ambiguous evidence:** 2 (CoinGecko, DeFiLlama)

## Repository contracts used for validation

- `docs/MARKET_INFORMATION_SOURCES_CONTRACT_V1.md`
- `docs/DATA_SOURCE_CONTRACT_V1.md`
- `docs/PHASE_1_2_SOURCE_BOUNDARY.md`
- `docs/information-sources-registry.md`
- `docs/information-source-verification-batch-001.md`
- `docs/information-source-verification-batch-002.md`
- `docs/information-source-verification-batch-003.md`
