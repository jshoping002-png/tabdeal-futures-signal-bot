# Source Operationalization Ledger — Reports 001–2040

## Purpose

This ledger operationalizes the existing source-verification history through report 2040.
It is not a new source-verification report. It records which already-documented source
families have a bounded adapter surface in code and which still require exact endpoint
or provider-contract work.

## Rules

- `DOCUMENTED` means the existing reports establish a public/documented source boundary,
  but no bounded adapter is claimed here.
- `ADAPTER_BUILT` means an existing read-only adapter class now provides an explicit,
  bounded envelope for the stated scope; it does not imply live verification or production readiness.
- No row authorizes strategy consumption.
- No row enables orders, accounts, balances, positions, leverage, or trade execution.
- Exact endpoints, series identifiers, PIT semantics, rate limits, reconnect behavior and
  provider failure semantics remain required wherever the underlying report left them unresolved.

## Existing source families

| Source | Verification record(s) | Lifecycle | Bounded adapter scope |
|---|---|---|---|
| Binance Futures Market Data | 001 | DOCUMENTED | Continuous-contract kline documentation only; exact project endpoint contract pending |
| Bybit Futures Market Data | 001, 2040 | ADAPTER_BUILT | Public REST kline; public REST orderbook |
| BLS Public Data API | 001 | ADAPTER_BUILT | Public JSON envelope; exact series/PIT contract runtime-configured |
| Binance Spot Market Data | 002 | DOCUMENTED | Public market-data boundary |
| Bybit Spot Market Data | 002 | ADAPTER_BUILT | Public REST kline with `category=spot` |
| U.S. Treasury Daily Interest-Rate Data | 002 | ADAPTER_BUILT | Official XML feed envelope |
| SEC EDGAR Public APIs | 002 | ADAPTER_BUILT | Public JSON submissions/XBRL envelope |
| OKX Market Data | 003 | DOCUMENTED | Public market-data endpoint family; exact project endpoint contract pending |
| Kraken Futures Market Data | 003 | DOCUMENTED | Public futures candles/analytics documented |
| Coinbase Advanced Trade Market Data | 003 | DOCUMENTED | Public Advanced Trade market-data boundary; derivatives not assumed |
| Deribit Market Data | 003 | DOCUMENTED | Public market-data boundary |
| CFTC Public Reporting / COT | 004 | ADAPTER_BUILT | Published feed/text envelope |
| CoinMarketCap Keyless Public API | 004 | ADAPTER_BUILT | Curated public JSON envelope; rate-limited |
| ECB Data Portal API | 005 | ADAPTER_BUILT | Public SDMX/text envelope |
| BIS Statistics API | 006 | ADAPTER_BUILT | Public SDMX/text envelope |
| Eurostat REST / SDMX APIs | 006 | ADAPTER_BUILT | Public REST/SDMX text envelope |
| OECD Data Explorer SDMX API | 007 | DOCUMENTED | Public SDMX endpoint family; exact dataset/series contract pending |
| NY Fed Markets Data APIs | 008 | DOCUMENTED | Public markets-data API family; route-by-route auth contract pending |

## Acceptance boundary

The report checkpoint through 2040 remains a verification-progress record; it explicitly
does not activate providers or production adapters. This ledger therefore moves only the
source families with an actual bounded code adapter to `ADAPTER_BUILT`. `LIVE_VERIFIED`,
`PRODUCTION_READY`, and `ACTIVE` are intentionally not asserted by this file.
