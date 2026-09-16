# Source Verification Batch 2041–2070

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

All records below are documentation-level verification only. The authoritative Bybit market-data documentation states that Tickers covers Spot, USDT, USDC, Inverse and Options, and documents the returned fields and their semantics. Instruments Info documents supported product categories, pagination, statuses, and instrument metadata. Funding Rate History documents historical funding-rate retrieval and millisecond funding timestamps. Current Bybit announcements also demonstrate that funding intervals and contract parameters can change over time, so such metadata must not be treated as immutable.

## Reports

2041. Bybit Tickers requires `category` and supports `spot`, `linear`, `inverse`, and `option`.
2042. Bybit Tickers accepts uppercase `symbol` values when the symbol parameter is supplied.
2043. Bybit Tickers returns `lastPrice` for linear/inverse contracts.
2044. Bybit Tickers returns `indexPrice` for linear/inverse contracts.
2045. Bybit Tickers returns `markPrice` for linear/inverse contracts.
2046. Bybit Tickers documents `prevPrice24h` as the market price 24 hours ago.
2047. Bybit Tickers documents `price24hPcnt` as the percentage change relative to 24 hours.
2048. Bybit Tickers documents `highPrice24h` as the highest price in the last 24 hours.
2049. Bybit Tickers documents `lowPrice24h` as the lowest price in the last 24 hours.
2050. Bybit Tickers documents `prevPrice1h` as the market price one hour ago.
2051. Bybit Tickers distinguishes `openInterest` as open-interest size on both sides.
2052. Bybit Tickers distinguishes `openInterestValue` as open-interest value on both sides.
2053. Bybit Tickers distinguishes `singleOpenInterest` as single-side open-interest size.
2054. Bybit Tickers distinguishes `singleOpenInterestValue` as single-side open-interest value.
2055. Bybit Tickers returns `turnover24h` for linear/inverse contracts.
2056. Bybit Tickers returns `volume24h` for linear/inverse contracts.
2057. Bybit Tickers documents `fundingRate` as the funding rate.
2058. Bybit Tickers documents `nextFundingTime` as the next funding time in milliseconds.
2059. Bybit Tickers documents `predictedDeliveryPrice` as having a value 30 minutes before delivery.
2060. Bybit Tickers documents `deliveryTime` as a millisecond delivery timestamp applicable to expiry futures only.
2061. Bybit Tickers documents `preOpenPrice` as an estimated pre-market contract open price and states it is meaningless once the market opens.
2062. Bybit Tickers documents `preQty` as estimated pre-market contract open quantity and states its value is meaningless once the market opens.
2063. Bybit Tickers documents `curPreListingPhase` as the current pre-market contract phase.
2064. Bybit Tickers documents `fundingIntervalHour` as the funding interval in hours and states the field currently supports whole hours.
2065. Bybit Tickers documents `fundingCap` as funding-rate upper and lower limits.
2066. Bybit Tickers documents `basisRateYear` as annual basis rate and states it is for Futures and blank for Perpetual.
2067. Bybit Instruments Info does not support pagination for Spot; `limit` and `cursor` are invalid for Spot.
2068. Bybit Instruments Info states that more than 500 linear symbols exist and that pagination is needed to retrieve all entries.
2069. Bybit Funding Rate History states that each symbol has a different funding interval and directs consumers to Instruments Info for that interval.
2070. Bybit Funding Rate History returns `fundingRateTimestamp` in milliseconds; current Bybit announcements also show that funding intervals can be adjusted for individual perpetual contracts, so interval metadata requires point-in-time handling rather than a permanent hard-coded assumption.

## Authorization boundary

None of these records authorizes a LONG/SHORT rule. No threshold, scoring rule, strategy input, provider activation, execution path, or automatic trading capability is added. PIT, provenance, validation, allowed-consumer, and Strategy Contract requirements remain mandatory.

## Sources

- Bybit Get Tickers: https://bybit-exchange.github.io/docs/v5/market/tickers
- Bybit Get Instruments Info: https://bybit-exchange.github.io/docs/v5/market/instrument
- Bybit Get Funding Rate History: https://bybit-exchange.github.io/docs/v5/market/history-fund-rate
- Bybit funding-interval adjustment examples: official Bybit announcements, July–August 2026.
