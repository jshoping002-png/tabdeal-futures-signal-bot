# Information Source Verification Batch 006

## Batch status

`FINAL — VALIDATED BEFORE COMMIT`

This batch adds only sources whose official documentation supports public programmatic access compatible with the project's read-only source policy. No existing source is removed, no provider is activated, no strategy rule is added, and no trading/execution capability is added.

## Record 001 — Bank for International Settlements (BIS) Statistics API

- **Source:** Bank for International Settlements (BIS) Statistics / BIS Data Portal.
- **Domain:** Global financial-system, monetary, banking, credit, derivatives and liquidity statistics.
- **Verified public API boundary:** BIS documents an SDMX RESTful API providing programmatic access to statistical data and metadata released to the public. The current API exposes GET data, availability, schema, structure and metadata operations.
- **Access/key assessment:** Official API documentation presents public GET endpoints and does not document an API-key or account-authentication parameter for the statistical data interface reviewed. BIS also states that its statistics can be freely exported from the Data Portal. This is sufficient for candidate source registration, but exact endpoint access behavior must still be tested in the provider-specific adapter contract before production use.
- **Verified data boundary:** BIS publishes international banking, debt securities, credit, global liquidity, derivatives, property prices, consumer prices, exchange rates, central-bank statistics and related financial-system datasets. BIS explicitly describes global liquidity indicators and international financial spillover/financial-stability uses.
- **Project value:** Independent global financial-context data can provide corroboration for macro/risk conditions, credit/liquidity context and cross-checks against exchange-derived observations. It is not a primary high-frequency crypto feed.
- **Project eligibility:** `CANDIDATE — PUBLIC API PATH VERIFIED`.
- **Production status:** `NOT ACTIVE`.
- **Reason:** Exact BIS datasets/series, release timestamps, update/revision behavior, query limits and Point-in-Time treatment must be specified before any decision use. BIS terms also reserve the right to limit or suspend API access.
- **Strategy use:** BIS data is contextual evidence only. Adding the source does not create a LONG/SHORT rule and cannot override the Strategy Contract.
- **Execution boundary:** No trading, account, order or execution endpoint is required or approved.
- **Official references:** https://stats.bis.org/api-doc/v2/ ; https://www.bis.org/statistics ; https://data.bis.org/help/export ; https://data.bis.org/help/legal

## Record 002 — Eurostat REST / SDMX APIs

- **Source:** Eurostat official statistical data APIs.
- **Domain:** European Union macroeconomic and financial statistics.
- **Verified public API boundary:** Eurostat documents REST APIs for Statistics, SDMX 3.0, SDMX 2.1 and catalogue access. The Statistics API is explicitly described as open for public use, and Eurostat states that its APIs provide free-of-charge programmatic access to statistical metadata and data.
- **Verified data boundary:** The APIs support public dataset discovery, metadata/structure queries, dimension-filtered data retrieval and multiple response formats including JSON-stat, SDMX-CSV, TSV and SDMX-ML. Official examples use direct REST URLs without an API key or authentication parameter.
- **Operational/revision limitation:** Eurostat states that datasets are updated twice daily when newer data or structural changes are available, but the database contains only the latest version and does not provide versioning or documentation of past versions. This is a material Point-in-Time limitation for signal use.
- **Project value:** Independent EU macroeconomic context and cross-checking for inflation, GDP, labor, trade, rates-related and other official statistical series. It complements ECB financial/macro data rather than replacing it.
- **Project eligibility:** `CANDIDATE — PUBLIC/FREE API PATH VERIFIED`.
- **Production status:** `NOT ACTIVE`.
- **Reason:** Exact dataset codes, publication/availability timing, latest-version-only behavior, rate/fair-use behavior and PIT handling must be specified before decision use. Historical replay must not assume access to superseded observations that Eurostat does not retain through this API.
- **Strategy use:** Eurostat data is contextual evidence only. Adding the source does not create a LONG/SHORT rule and cannot override the Strategy Contract.
- **Execution boundary:** No trading, account, order or execution endpoint is required or approved.
- **Official references:** https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-introduction ; https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-getting-started ; https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-detailed-guidelines/sdmx2-1/data-query ; https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-detailed-guidelines/asynchronous-api

## Batch validation result

- **Records produced:** 2
- **Records requiring correction during validation:** 0
- **Records finally approved for source-list addition:** 2
- **Source-list removals:** 0
- **Provider activations:** 0
- **Strategy rules added:** 0
- **Order/execution capabilities added:** 0
- **Sources deferred:** 0

## Repository contracts used for validation

- `docs/MARKET_INFORMATION_SOURCES_CONTRACT_V1.md`
- `docs/DATA_SOURCE_CONTRACT_V1.md`
- `docs/PHASE_1_2_SOURCE_BOUNDARY.md`
- `docs/PIT_SNAPSHOT_CONTRACT_V1.md`
- `docs/information-sources-registry.md`
- `docs/information-source-verification-batch-005.md`
