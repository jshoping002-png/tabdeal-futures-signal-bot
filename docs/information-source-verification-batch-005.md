# Information Source Verification Batch 005

## Batch status

`FINAL — VALIDATED BEFORE COMMIT`

This batch adds only a source whose official documentation verifies a public programmatic data interface compatible with the project source policy. No source is removed, no provider is activated, no strategy rule is added, and no trading/execution capability is added.

## Record 001 — European Central Bank Data Portal API

- **Source:** European Central Bank (ECB) Data Portal.
- **Domain:** Official macroeconomic, financial-market and exchange-rate data.
- **Verified public API boundary:** ECB documents an SDMX 2.1 RESTful web service at `https://data-api.ecb.europa.eu/service/` for programmatic retrieval of data and metadata. Official examples show direct HTTP retrieval without an API key or authentication parameter.
- **Verified data boundary:** The API supports exchange rates and broad ECB statistical datasets. Series can be queried by explicit dimensions and date ranges.
- **Verified revision/history behavior:** `updatedAfter` retrieves observations added, revised or deleted after a supplied timestamp. `includeHistory=true` returns the current production version and previous versions. This is directly relevant to the project's PIT and replay requirements.
- **Verified formats:** Official documentation supports JSON, CSV and SDMX formats.
- **Project value:** Provides an independent official macro/financial context source, including euro exchange rates and other financial/economic series, which can be used for context, cross-checking and risk evaluation after exact series contracts are defined.
- **Project eligibility:** `CANDIDATE — PUBLIC API PATH VERIFIED`.
- **Production status:** `NOT ACTIVE`.
- **Reason:** Exact series IDs, publication/availability timing, revision/PIT policy and rate/operational limits must be specified in a provider-specific contract before decision use.
- **Strategy use:** ECB data is contextual evidence only. Adding the source does not create a LONG/SHORT rule and cannot override the Strategy Contract.
- **Execution boundary:** No trading, account, order or execution endpoint is required or approved.
- **Official references:** https://data.ecb.europa.eu/help/api/overview ; https://data.ecb.europa.eu/help/api/data ; https://data.ecb.europa.eu/help/data-examples

## Batch validation result

- **Records produced:** 1
- **Records requiring correction during validation:** 0
- **Records finally approved for source-list addition:** 1
- **Source-list removals:** 0
- **Provider activations:** 0
- **Strategy rules added:** 0
- **Order/execution capabilities added:** 0
- **Sources deferred:** 0

## Repository contracts used for validation

- `docs/MARKET_INFORMATION_SOURCES_CONTRACT_V1.md`
- `docs/DATA_SOURCE_CONTRACT_V1.md`
- `docs/PHASE_1_2_SOURCE_BOUNDARY.md`
- `docs/information-sources-registry.md`
- `docs/information-source-verification-batch-004.md`
