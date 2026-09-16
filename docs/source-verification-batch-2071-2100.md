# Source Verification Batch 2071–2100

## Status

- Batch size: 30
- Reports produced: 30
- Reports corrected: 0
- Reports finally approved: 30
- Sources removed: 0
- Sources replaced: 0
- Providers activated: 0
- Strategy rules added: 0
- Code/config/dependency changes: 0
- Execution/trading capability added: 0

## Evidence basis

Documentation-level verification only. Official Bybit documentation was checked for Tickers, Instruments Info, Funding Rate History, Delivery Price, Delivery Record, and the public WebSocket Ticker specification. These records do not activate any provider or authorize any strategy input.

## Reports

2071. Bybit REST Tickers is a latest-price snapshot endpoint covering Spot, USDT contracts, USDC contracts, Inverse contracts, and Options.
2072. Bybit REST Tickers requires the `category` parameter.
2073. For Options, Bybit Tickers requires either `symbol` or `baseCoin`.
2074. Bybit Tickers documents `bid1Price` as best bid price for linear/inverse responses.
2075. Bybit Tickers documents `ask1Price` as best ask price for linear/inverse responses.
2076. Bybit Tickers documents `bid1Size` as best bid size for linear/inverse responses.
2077. Bybit Tickers documents `ask1Size` as best ask size for linear/inverse responses.
2078. Best bid/ask fields are quote-state observations and are not automatically equivalent to a complete order-book snapshot.
2079. Bybit WebSocket Ticker documentation identifies pre-market fields separately from continuous-trading state.
2080. Bybit WebSocket Ticker documents that `preOpenPrice` becomes meaningless when continuous trading begins.
2081. Bybit WebSocket Ticker documents that `preQty` becomes meaningless when continuous trading begins.
2082. Bybit WebSocket Ticker documents `fundingIntervalHour` as a whole-hour value for perpetual contracts.
2083. Bybit WebSocket Ticker documents `fundingCap` as the funding-rate upper and lower limits for perpetual contracts.
2084. Bybit WebSocket Ticker documents `basisRateYear` as annual basis rate for Futures and not for Perpetual.
2085. Bybit Instruments Info exposes `fundingInterval` as a funding interval in minutes.
2086. Bybit Instruments Info exposes `upperFundingRate` and `lowerFundingRate` as funding-rate limits.
2087. Bybit Instruments Info exposes `launchTime` as instrument launch timestamp metadata.
2088. Bybit Instruments Info exposes `deliveryTime` as instrument delivery timestamp metadata where applicable.
2089. Bybit Instruments Info supports instrument `status` filtering, including states such as PreLaunch, Trading, Settling, Delivering, and Closed.
2090. Bybit Instruments Info documents a default limit of 500 and a maximum of 1000 for the relevant market categories; Spot does not have pagination.
2091. Instrument pagination is therefore required when the returned dataset exceeds one page for categories that support pagination.
2092. A missing or changed instrument-status record must not be silently treated as Trading.
2093. A delivery timestamp is instrument metadata and is not itself a market-price observation.
2094. Bybit Funding Rate History covers USDT and USDC perpetuals and Inverse perpetuals.
2095. Funding Rate History requires `category` and uppercase `symbol`.
2096. Funding Rate History allows optional `startTime` and `endTime` in milliseconds; passing only `startTime` is documented as an error.
2097. Funding Rate History returns up to 200 records per page by default and supports a limit from 1 to 200.
2098. Funding Rate History returns `fundingRateTimestamp` in milliseconds and `fundingRate` as the funding-rate value.
2099. Bybit Delivery Price covers USDT Futures, USDC Futures, Inverse Futures, and Options; the endpoint also warns that extreme volatility can cause increased latency or temporary delivery delays.
2100. Bybit Delivery Record returns delivery records for Inverse Futures, USDC Futures, USDT Futures, and Options, sorted by `deliveryTime` descending; its time-range rules are documentation-defined and must not be replaced by an assumed fixed window.

## Authorization boundary

None of these records authorizes a LONG/SHORT rule. No threshold, score, signal rule, provider activation, execution path, order endpoint, private credential, or automatic trading capability is added. PIT, provenance, validation, allowed-consumer, and Strategy Contract requirements remain mandatory.

## Sources

- https://bybit-exchange.github.io/docs/v5/market/tickers
- https://bybit-exchange.github.io/docs/v5/websocket/public/ticker
- https://bybit-exchange.github.io/docs/v5/market/instrument
- https://bybit-exchange.github.io/docs/v5/market/history-fund-rate
- https://bybit-exchange.github.io/docs/v5/market/delivery-price
- https://bybit-exchange.github.io/docs/v5/asset/delivery
