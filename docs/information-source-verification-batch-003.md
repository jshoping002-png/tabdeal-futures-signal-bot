# Information Source Verification Batch 003

## Batch status

`FINAL — VALIDATED BEFORE COMMIT`

This batch records only evidence verified against official provider documentation and the repository source contracts. It does not activate any provider, add strategy rules, remove any source, or add trading/execution capability.

## Record 001 — OKX Market Data

- **Source:** OKX official API documentation.
- **Domain:** Crypto spot and derivatives market data.
- **Verified public-data boundary:** OKX documents public market-data endpoints that do not require authentication. The official API agreement lists public market data including tickers, order books, trades, candlesticks/OHLCV, funding rates, index prices, mark prices, open interest and other market-data categories.
- **Verified rate-limit boundary:** OKX documents IP-based rate limits for public unauthenticated REST market-data endpoints, with endpoint-specific limits.
- **Availability caveat:** OKX documents regional API domains and jurisdiction/service availability differences; this must be treated as provider availability behavior, not bypassed.
- **Project eligibility:** `CANDIDATE — PUBLIC MARKET-DATA PATH VERIFIED`.
- **Production status:** `NOT ACTIVE`.
- **Reason:** Exact selected endpoint set, response schema, timestamps, historical coverage/pagination, reconnect behavior and PIT semantics must be contracted before production activation.
- **Strategy use:** No strategy consumption is approved merely because a field is publicly available. Order-book/liquidation/derivatives fields remain outside strategy logic unless the Strategy Contract explicitly approves them.
- **Execution boundary:** No private/account/order/execution endpoint is approved.
- **Official references:** https://www.okx.com/docs-v5/en/ ; https://tr.okx.com/en/help/okx-api-agreement

## Record 002 — Kraken Futures Market Data

- **Source:** Kraken Futures official API documentation.
- **Domain:** Crypto futures market data and public analytics.
- **Verified candle path:** `GET https://futures.kraken.com/api/charts/v1/:tick_type/:symbol/:resolution` supports public chart candles. Documented tick types include `spot`, `mark` and `trade`; documented resolutions include 1m, 5m, 15m, 30m, 1h, 4h, 12h, 1d and 1w. The documented response includes OHLC, volume and a `more_candles` indicator.
- **Verified analytics path:** Kraken documents a public market-analytics path with analytics types including open interest, aggressor differential, trade volume/count, liquidation volume, rolling volatility, long/short ratio, CVD, order book, spreads, liquidity, slippage, future basis and funding.
- **Authentication evidence:** The reviewed public GET examples and documentation expose these market-data/chart paths without private-account authentication.
- **Project eligibility:** `CANDIDATE — PUBLIC FUTURES DATA PATH VERIFIED`.
- **Production status:** `NOT ACTIVE`.
- **Reason:** Exact endpoint allowlist, rate limits, timestamp/availability semantics, historical behavior and PIT treatment require a provider-specific contract before activation.
- **Strategy use:** Public analytics are inputs only; no analytics item is automatically a LONG/SHORT rule. Any derivatives/order-flow use requires explicit Strategy Contract approval.
- **Execution boundary:** No order, account, position or execution endpoint is approved.
- **Official references:** https://docs.kraken.com/api/docs/futures-api/charts/candles ; https://docs.kraken.com/api/docs/futures-api/charts/market-analytics

## Record 003 — Coinbase Advanced Trade Market Data

- **Source:** Coinbase Advanced Trade official API documentation.
- **Domain:** Public spot/market-data interface.
- **Verified REST boundary:** Coinbase documents that public Advanced Trade endpoints do not require authentication and includes public products, product book, public candles and public market trades.
- **Verified WebSocket boundary:** Coinbase documents the public Advanced Trade market-data WebSocket endpoint. Public market-data channels include heartbeats, candles, status, ticker, ticker batch, level2 and market trades; user/futures-balance channels require authentication.
- **Verified operational behavior:** Coinbase documents unauthenticated WebSocket message and connection rate limits, and documents sequence numbers plus dropped/out-of-order message handling requirements for streaming consumers.
- **Critical scope limitation:** This evidence verifies public Advanced Trade market-data paths but does **not** establish the project-required Coinbase Futures/Derivatives data path. No derivatives eligibility is inferred from the spot/public market-data documentation.
- **Project eligibility:** `CANDIDATE — PUBLIC MARKET-DATA PATH VERIFIED`.
- **Production status:** `NOT ACTIVE`.
- **Reason:** Exact project-required product scope, endpoint allowlist, rate limits, historical coverage, reconnect/gap handling and PIT semantics must be contracted. Futures/derivatives eligibility remains unresolved.
- **Strategy use:** No strategy consumption is approved.
- **Execution boundary:** No private/account/order/execution endpoint is approved.
- **Official references:** https://docs.cdp.coinbase.com/advanced-trade/docs/rest-api ; https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/websocket/websocket-overview ; https://docs.cdp.coinbase.com/coinbase-business/advanced-trade-apis/websocket/websocket-channels

## Record 004 — Deribit Market Data

- **Source:** Deribit official API documentation.
- **Domain:** Crypto futures/options/spot public market data.
- **Verified public access:** Deribit’s official quickstart explicitly shows public market-data calls without authentication, including `public/get_instruments`, `public/ticker` and `public/get_order_book`.
- **Verified instrument path:** `public/get_instruments` exposes instrument metadata for future, option, spot and combo kinds, including instrument name, timestamps, state and other instrument attributes. The method has a documented sustained rate of 1 request/second.
- **Verified candle path:** `public/get_tradingview_chart_data` is documented as publicly available market data with start/end timestamps and supported resolutions from 1 minute through daily. The response provides timestamp ticks and OHLC/volume arrays.
- **Verified order-book path:** `public/get_order_book` exposes timestamped order-book data plus open interest, mark price, index price, funding fields and bid/ask levels. This source is evidence of data availability only; it does not authorize those fields for strategy use.
- **Rate-limit evidence:** Deribit documents a credit-based rate-limiting system and explicitly lists a 1 request/second sustained rate for `public/get_instruments`; other method limits are method-specific.
- **Project eligibility:** `CANDIDATE — PUBLIC MARKET-DATA PATH VERIFIED`.
- **Production status:** `NOT ACTIVE`.
- **Reason:** Exact selected endpoint set, endpoint-specific limits for all required methods, historical coverage, timestamp semantics, reconnect behavior and PIT handling still require a provider-specific project contract.
- **Strategy use:** No order-book, funding, open-interest, options or other derivatives field is automatically admitted to Strategy. Explicit Strategy Contract approval is required.
- **Execution boundary:** No private/account/order/execution endpoint is approved. The project must not create or use trading credentials for this source.
- **Official references:** https://docs.deribit.com/articles/deribit-quickstart ; https://docs.deribit.com/api-reference/market-data/public-get_instruments ; https://docs.deribit.com/api-reference/market-data/public-get_tradingview_chart_data ; https://docs.deribit.com/api-reference/market-data/public-get_order_book ; https://docs.deribit.com/articles/rate-limits

## Batch validation result

The four records were validated together before commit against the repository source registry/contracts and the official provider documentation cited in each record.

- **Records produced:** 4
- **Records requiring correction during validation:** 0
- **Records finally approved for this batch:** 4
- **Source-list removals:** 0
- **Provider activations:** 0
- **Strategy rules added:** 0
- **Order/execution capabilities added:** 0
- **Unsupported items left explicitly unresolved:** exact OKX endpoint contracts and PIT semantics; exact Kraken endpoint limits and PIT semantics; Coinbase Futures/Derivatives path verification; exact Deribit endpoint limits for all required methods, historical/reconnect semantics and PIT contract.

## Repository contracts used for validation

- `docs/MARKET_INFORMATION_SOURCES_CONTRACT_V1.md`
- `docs/DATA_SOURCE_CONTRACT_V1.md`
- `docs/PHASE_1_2_SOURCE_BOUNDARY.md`
- `docs/information-sources-registry.md`
- `docs/information-source-verification-batch-001.md`
- `docs/information-source-verification-batch-002.md`
