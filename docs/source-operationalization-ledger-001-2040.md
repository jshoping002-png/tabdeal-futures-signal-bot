# Source Operationalization Ledger — Reports 001–2040

This ledger records operationalization of the existing source-verification history. It is not a new source-verification report.

| Source | Reports | Lifecycle | Read-only implementation scope |
|---|---|---|---|
| Binance Futures Market Data | 001 | ADAPTER_BUILT | Coin-M continuous-contract klines |
| Bybit Futures Market Data | 001, 2040 | ADAPTER_BUILT | Kline, orderbook, open interest, funding history, tickers, instruments info |
| BLS Public Data API | 001 | ADAPTER_BUILT | Public JSON envelope; exact series/PIT contract runtime-configured |
| Binance Spot Market Data | 002 | DOCUMENTED | Exact project endpoint contract pending |
| Bybit Spot Market Data | 002 | ADAPTER_BUILT | Public kline and ticker paths |
| U.S. Treasury Daily Interest-Rate Data | 002 | ADAPTER_BUILT | Official XML feed envelope |
| SEC EDGAR Public APIs | 002 | ADAPTER_BUILT | Public JSON submissions/XBRL envelope |
| OKX Market Data | 003 | DOCUMENTED | Exact endpoint/schema/PIT contract pending |
| Kraken Futures Market Data | 003 | ADAPTER_BUILT | Public chart candles for documented tick types/resolutions |
| Coinbase Advanced Trade Market Data | 003 | DOCUMENTED | Public Advanced Trade boundary; derivatives not assumed |
| Deribit Market Data | 003 | ADAPTER_BUILT | Public JSON-RPC: get_instruments, ticker, order book, TradingView chart data |
| CFTC Public Reporting / COT | 004 | ADAPTER_BUILT | Published feed/text envelope |
| CoinMarketCap Keyless Public API | 004 | ADAPTER_BUILT | Curated public JSON envelope; rate-limited |
| ECB Data Portal API | 005 | ADAPTER_BUILT | Public SDMX/text envelope |
| BIS Statistics API | 006 | ADAPTER_BUILT | Public SDMX/text envelope |
| Eurostat REST / SDMX APIs | 006 | ADAPTER_BUILT | Public REST/SDMX text envelope |
| OECD Data Explorer SDMX API | 007 | DOCUMENTED | Exact dataset/series contract pending |
| NY Fed Markets Data APIs | 008 | DOCUMENTED | Route-by-route auth/availability contract pending |

No source is marked `LIVE_VERIFIED`, `PRODUCTION_READY`, or `ACTIVE`. No source row authorizes strategy use or trading execution.
