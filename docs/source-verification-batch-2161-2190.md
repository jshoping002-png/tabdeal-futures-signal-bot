# Source Verification Batch 2161–2190

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

Documentation-level verification using the official public Bybit documentation repository (`bybit-exchange/docs`), snapshot commit `75994fda16e052aaad6e3fade82fd1f6fd90288e`. The batch covers the official Tickers, Instruments Info, and Rate Limit documentation. These records are source evidence only and do not activate any provider or authorize any strategy input.

## Reports

2161. Bybit `Get Tickers` covers Spot, USDT contracts, USDC contracts, Inverse contracts, and Options.
2162. Bybit `Get Tickers` requires `category`, with values `spot`, `linear`, `inverse`, and `option`.
2163. In Bybit `Get Tickers`, `symbol` is optional and must use uppercase format when supplied.
2164. In Bybit `Get Tickers`, `baseCoin` is option-only and must use uppercase format.
2165. In Bybit `Get Tickers`, `expDate` applies to Options only.
2166. Bybit `Get Tickers` documents `lastPrice` as the last-price field for linear and inverse market responses.
2167. Bybit `Get Tickers` exposes `indexPrice` and `markPrice` as separate fields.
2168. Bybit `Get Tickers` exposes `openInterest` and `openInterestValue` as the both-sides open-interest size and value fields for linear/inverse responses.
2169. Bybit `Get Tickers` documents `fundingRate` as the funding-rate field and `nextFundingTime` as the next funding time in milliseconds.
2170. Bybit `Get Tickers` documents `deliveryTime` for expiry futures and states that `predictedDeliveryPrice` has a value 30 minutes before delivery.
2171. Bybit `Get Instruments Info` covers Spot, USDT contracts, USDC contracts, Inverse contracts, and Options.
2172. Bybit `Get Instruments Info` states that Spot does not support pagination, so `limit` and `cursor` are invalid for Spot.
2173. Bybit documents that there are now more than 500 linear symbols and that cursor/limit must be used to retrieve all entries.
2174. Bybit `Get Instruments Info` documents `limit` from 1 to 1000, with a default of 500.
2175. Bybit documents instrument-status defaults: linear/inverse/spot return Trading and PendingOpen by default; options return PreLaunch, Trading, and Delivering; Spot has Trading only.
2176. Bybit documents `baseCoin` for linear, inverse, and option categories, with `baseCoin=All` valid only for Options.
2177. Bybit `Get Instruments Info` exposes `launchTime` as a launch timestamp in milliseconds.
2178. Bybit `Get Instruments Info` exposes `deliveryTime` in milliseconds for expiry-futures delivery time and, where applicable, perpetual delisting time.
2179. Bybit `Get Instruments Info` exposes `fundingInterval` as an integer funding interval in minutes.
2180. Bybit documents that `maxLimitOrderQty`, `maxMarketOrderQty`, and `postOnlyMaxLimitOrderSize` are adjusted bi-monthly and should not be assumed constant.
2181. Bybit documents a default HTTP IP limit of 600 requests within a 5-second window per IP.
2182. Bybit states that HTTP `403, access too frequent` indicates exceeded request frequency and instructs clients to terminate HTTP sessions and wait at least 10 minutes.
2183. Bybit advises against operating at the edge of the documented HTTP limits because abnormal network activity can cause an unexpected violation.
2184. Bybit documents that clients should not establish more than 500 WebSocket connections within a 5-minute window.
2185. Bybit advises clients not to frequently connect and disconnect WebSocket sessions.
2186. Bybit documents a maximum of 1,000 market-data WebSocket connections per IP.
2187. Bybit states that market-data WebSocket connection limits are counted separately for Spot, Linear, Inverse, and Options markets.
2188. Bybit documents API rate limiting as a rolling time window per second and UID.
2189. Bybit documents the response headers `X-Bapi-Limit-Status`, `X-Bapi-Limit`, and `X-Bapi-Limit-Reset-Timestamp` for rate-limit state.
2190. Bybit documents `retCode` 10006 with `retMsg` `Too many visits!` as an API rate-limit response.

## Authorization boundary

None of these records authorizes a LONG/SHORT rule. No threshold, score, signal rule, provider activation, execution path, order endpoint, private credential, or automatic trading capability is added. These records are documentation evidence for future read-only adapter design. PIT timing, provenance, schema validation, failure handling, and explicit consumer authorization remain mandatory.

## Sources

- https://github.com/bybit-exchange/docs/blob/75994fda16e052aaad6e3fade82fd1f6fd90288e/docs/v5/market/tickers.mdx
- https://github.com/bybit-exchange/docs/blob/75994fda16e052aaad6e3fade82fd1f6fd90288e/docs/v5/market/instrument.mdx
- https://github.com/bybit-exchange/docs/blob/75994fda16e052aaad6e3fade82fd1f6fd90288e/docs/v5/rate-limit/rate-limit.mdx
