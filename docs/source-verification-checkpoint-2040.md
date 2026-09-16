# Source Verification Checkpoint — 2040

## Purpose

This file records a project-progress checkpoint for the source-verification work completed through report **2040**. It is a verification-progress record only; it does not activate providers, strategy inputs, execution paths, or production adapters.

## Checkpoint status

- Verification reports completed through: **2040**
- Batch size: **30 reports**
- Latest completed batch: **2011–2040**
- Reports produced in latest batch: **30**
- Reports corrected in latest batch: **0**
- Reports finally approved in latest batch: **30**
- Sources removed: **0**
- Sources replaced: **0**
- Providers activated: **0**
- Strategy rules added: **0**
- Code/config/dependency changes: **0**
- Execution/trading capability added: **0**

## Scope boundary

The checkpoint does not change the authoritative source registry. The registry remains the source-of-record for planned information sources and explicitly keeps external market-data access read-only. Source registration, data-domain classification, field-level authorization, PIT validation, Strategy Contract authorization, and provider activation remain separate controls.

No source is removed or replaced by this checkpoint.

## Verification evidence used for the latest Bybit market-data work

Official Bybit documentation currently documents:

- Open Interest for USDT, USDC and Inverse contracts, with category/symbol/interval requirements, millisecond timestamps, pagination, and separate `openInterest` and `singleOpenInterest` fields.
- Instruments Info for Spot, USDT, USDC, Inverse and Options, including pagination behavior, instrument status, launch/delivery timestamps and metadata fields.
- Tickers for latest price, index/mark price, 24-hour volume/turnover, funding, open-interest fields and expiry/pre-market metadata.
- Funding Rate History with millisecond `fundingRateTimestamp` and symbol-specific funding intervals.

Official references:

- https://bybit-exchange.github.io/docs/v5/market/open-interest
- https://bybit-exchange.github.io/docs/v5/market/instrument
- https://bybit-exchange.github.io/docs/v5/market/tickers
- https://bybit-exchange.github.io/docs/v5/market/history-fund-rate

## Authorization boundary

These documented fields remain **not automatically authorized as LONG/SHORT strategy inputs**. A field can only enter decision logic after the applicable Strategy Contract, PIT/timing, provenance, validation, and allowed-consumer requirements are satisfied.

The project remains **read-only** and has **no automatic trading/execution path**.

## Continuation point

The next verification batch begins at **2041** and must remain in batches of **30**.
