# Source Verification Batch 2191–2220

## Status

- Batch size: 30
- Reports produced: 30
- Reports corrected during validation: 0
- Reports finally approved: 30
- Sources removed: 0
- Sources replaced: 0
- Providers activated: 0
- Strategy rules added: 0
- Code/config/dependency changes: 0
- Execution/trading capability added: 0

## Evidence basis

Documentation-level verification using the official public Bybit documentation repository (`bybit-exchange/docs`), snapshot commit `75994fda16e052aaad6e3fade82fd1f6fd90288e`. The batch covers the official REST Orderbook, Recent Public Trades, and public WebSocket Trade documentation. These records are source evidence only and do not activate any provider or authorize any strategy input.

## Reports

2191. Bybit `Get Orderbook` covers Spot, USDT contracts, USDC contracts, Inverse contracts, and Options.
2192. Bybit `Get Orderbook` documents 1000-level orderbook data for contracts and Spot, and 25-level orderbook data for Options.
2193. Bybit states that the REST Orderbook response is in snapshot format.
2194. Bybit states that Retail Price Improvement (RPI) orders are not included in the REST Orderbook response and are not visible over the API.
2195. Bybit `Get Orderbook` requires `category` and documents `spot`, `linear`, `inverse`, and `option` as the product-type values.
2196. Bybit `Get Orderbook` requires `symbol` and documents uppercase symbol format, such as `BTCUSDT`.
2197. Bybit documents the REST Orderbook `limit` range for Spot as 1–1000, with default 1.
2198. Bybit documents the REST Orderbook `limit` range for linear and inverse contracts as 1–1000, with default 25.
2199. Bybit documents the REST Orderbook `limit` range for Options as 1–25, with default 1.
2200. Bybit documents REST Orderbook bid entries as buyer quotes sorted by price in descending order.
2201. Bybit documents REST Orderbook ask entries as seller quotes sorted by price in ascending order.
2202. Bybit documents `ts` in REST Orderbook as the system-generated data timestamp in milliseconds.
2203. Bybit documents REST Orderbook `u` as an update ID and states that it is always in sequence.
2204. Bybit documents REST Orderbook `seq` as a cross sequence that can be used to compare different orderbook levels, with the smaller sequence representing data generated earlier.
2205. Bybit documents REST Orderbook `cts` as the timestamp from the matching engine when the orderbook data is produced.
2206. Bybit states that REST Orderbook `cts` can be correlated with `T` from the public trade channel.
2207. Bybit `Get Recent Public Trades` covers Spot, USDT contracts, USDC contracts, Inverse contracts, and Options.
2208. Bybit `Get Recent Public Trades` documents `symbol` as required for Spot, linear, and inverse requests.
2209. Bybit documents `symbol` as optional for Options in `Get Recent Public Trades`.
2210. Bybit documents `baseCoin` as option-only for Recent Public Trades and states that when omitted, BTC data is returned by default.
2211. Bybit documents `optionType` as option-only with values `Call` or `Put` for Recent Public Trades.
2212. Bybit documents the Recent Public Trades `limit` range for Spot as 1–60, with default 60.
2213. Bybit documents the Recent Public Trades `limit` range for non-Spot categories as 1–1000, with default 500.
2214. Bybit documents `execId` in Recent Public Trades as the execution ID.
2215. Bybit documents the Recent Public Trades `time` field as trade time in milliseconds.
2216. Bybit documents `isBlockTrade` as the flag indicating whether a trade is a block trade.
2217. Bybit documents `isRPITrade` as the flag indicating whether a trade is an RPI trade.
2218. Bybit documents `seq` in Recent Public Trades as the cross sequence.
2219. Bybit's public WebSocket Trade stream is pushed in real time after subscription.
2220. Bybit's public WebSocket Trade topic is `publicTrade.{symbol}`; for Options, the topic uses `baseCoin` instead of a symbol.

## Authorization boundary

None of these records authorizes a LONG/SHORT rule. No threshold, score, signal rule, provider activation, execution path, order endpoint, private credential, or automatic trading capability is added. These records are documentation evidence for future read-only adapter design. PIT timing, provenance, schema validation, failure handling, and explicit consumer authorization remain mandatory.

## Sources

- https://github.com/bybit-exchange/docs/blob/75994fda16e052aaad6e3fade82fd1f6fd90288e/docs/v5/market/orderbook.mdx
- https://github.com/bybit-exchange/docs/blob/75994fda16e052aaad6e3fade82fd1f6fd90288e/docs/v5/market/recent-trade.mdx
- https://github.com/bybit-exchange/docs/blob/75994fda16e052aaad6e3fade82fd1f6fd90288e/docs/v5/websocket/public/trade.mdx
