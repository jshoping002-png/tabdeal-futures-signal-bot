# Source Verification Batch 2221–2250

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

Documentation-level verification using the official public Bybit documentation repository (`bybit-exchange/docs`), snapshot commit `75994fda16e052aaad6e3fade82fd1f6fd90288e`. This batch covers Funding Rate History and Open Interest market-data documentation. These records are source evidence only and do not activate any provider or authorize any strategy input.

## Reports

2221. Bybit `Get Funding Rate History` provides historical funding-rate data.
2222. Bybit states that each symbol can have a different funding interval.
2223. Bybit documents that, for an example 8-hour funding interval at UTC 12, the returned latest funding rate is the one settled at UTC 8.
2224. Bybit directs clients to the `instruments-info` endpoint to query a symbol's funding-rate interval.
2225. Funding Rate History covers USDT and USDC perpetual and Inverse perpetual products.
2226. Funding Rate History uses the public HTTP endpoint `/v5/market/funding/history`.
2227. Funding Rate History requires `category`, with documented values `linear` and `inverse`.
2228. Funding Rate History requires `symbol`, using uppercase symbol format.
2229. Funding Rate History supports optional `startTime` and `endTime` timestamps in milliseconds.
2230. Funding Rate History documents `limit` from 1 to 200 with a default of 200.
2231. Bybit documents that passing only `startTime` to Funding Rate History returns an error.
2232. Bybit documents that passing only `endTime` returns up to 200 records through `endTime`.
2233. Bybit documents that passing neither `startTime` nor `endTime` returns up to 200 records through the current time.
2234. Funding Rate History responses expose `category` and a `list` of funding-rate records.
2235. Each Funding Rate History record exposes `symbol`, `fundingRate`, and `fundingRateTimestamp`, with the timestamp in milliseconds.
2236. Bybit `Get Open Interest` provides open-interest data for each symbol.
2237. Open Interest covers USDT contract, USDC contract, and Inverse contract products.
2238. Open Interest uses the public HTTP endpoint `/v5/market/open-interest`.
2239. Open Interest requires `category`, with documented values `linear` and `inverse`.
2240. Open Interest requires an uppercase `symbol`.
2241. Open Interest requires `intervalTime`, with documented values `5min`, `15min`, `30min`, `1h`, `4h`, and `1d`.
2242. Open Interest supports optional `startTime` and `endTime` timestamps in milliseconds.
2243. Open Interest documents `limit` from 1 to 200 with a default of 50.
2244. Open Interest supports a `cursor` parameter for pagination.
2245. Open Interest response records expose `openInterest` as the sum of both sides.
2246. Open Interest response records expose `singleOpenInterest` as the single-side value.
2247. Bybit documents that the unit of `openInterest` may differ by instrument type, giving BTCUSD inverse as USD and BTCUSDT linear as BTC.
2248. Each Open Interest record exposes a `timestamp` in milliseconds.
2249. Open Interest responses expose `nextPageCursor` for pagination.
2250. Bybit states that the upper queryable time limit is the symbol launch time and warns that extreme market volatility can increase latency or temporarily delay data delivery.

## Authorization boundary

None of these records authorizes a LONG/SHORT rule. No threshold, score, signal rule, provider activation, execution path, order endpoint, private credential, or automatic trading capability is added. These records are documentation evidence for future read-only adapter design. PIT timing, provenance, schema validation, failure handling, pagination integrity, and explicit consumer authorization remain mandatory.

## Sources

- https://github.com/bybit-exchange/docs/blob/75994fda16e052aaad6e3fade82fd1f6fd90288e/docs/v5/market/history-fund-rate.mdx
- https://github.com/bybit-exchange/docs/blob/75994fda16e052aaad6e3fade82fd1f6fd90288e/docs/v5/market/open-interest.mdx
