# Market Information Sources Contract V1

## Status
DESIGNED — source inventory and boundary contract

## Purpose
Define the approved information-source classes for market analysis without inventing trading rules or requiring paid/API-key-only providers.

## Source policy

A production source is eligible only when its required data can be obtained through a public interface without API key/secret or user-account authentication. Provider-specific limits, schemas, timestamp semantics, and availability must be verified before activation.

## Source classes

### 1. Primary exchange market data

Reference exchange sources include:
- Binance public market-data interfaces;
- Bybit public market-data interfaces;
- OKX public market-data interfaces;
- Kraken public market-data interfaces;
- Coinbase public market-data interfaces;
- Deribit public market-data interfaces, including derivatives/options market data.

Potential data classes include OHLCV, trades, order book, mark/index price, funding, open interest, liquidations, and other public derivatives fields only where the provider exposes them without authentication.

### 2. On-chain and whale intelligence

Use public blockchain data and unauthenticated public endpoints where available to derive:
- large transfers;
- exchange deposits/withdrawals;
- exchange-balance changes;
- large-address activity;
- stablecoin flows;
- accumulation/distribution indicators.

A whale observation is an information input, not by itself a LONG/SHORT rule.

### 3. Derivatives and order-flow intelligence

Where public unauthenticated exchange data supports them, collect:
- open interest;
- funding;
- liquidations;
- taker buy/sell flow;
- trade flow/CVD-derived measurements;
- order-book liquidity and imbalance;
- basis/mark/index relationships;
- public options metrics where available.

### 4. Macro/economic information

Use public official sources without API-key requirements where possible, including:
- Federal Reserve public information;
- U.S. BLS public data/API access;
- U.S. BEA public data where accessible without a key;
- ECB public data/API access;
- equivalent official central-bank/statistical sources for other relevant economies.

Relevant information classes include interest-rate decisions, inflation, employment/unemployment, payrolls, GDP, PMI, retail sales, central-bank communications, and scheduled economic events.

### 5. Risk and market-context information

Potential public inputs include DXY, VIX, Treasury yields, major equity indices, gold, volatility, breadth, and liquidity/financial-condition measures where public unauthenticated access is available.

These are context/risk inputs unless a separate contract explicitly assigns them decision semantics.

### 6. News and event information

Use public, unauthenticated sources for material crypto, regulatory, exchange, ETF, security, geopolitical, and macroeconomic events where technically and legally appropriate.

News must carry source timestamp/availability metadata sufficient for point-in-time use. No post-decision article may influence a decision.

## TradingView boundary

TradingView is recognized as a market-analysis/reference platform, but it is not assumed to be a production API source merely because public charts are viewable. Any programmatic TradingView data path requires separate verification of public unauthenticated access and licensing/usage terms before activation.

## Point-in-time requirements

Every information source used in a decision must expose sufficient timing metadata to establish that the information was available before the decision/reference boundary. Missing or ambiguous timing means BLOCKED for any decision use.

## Provider independence

Multiple exchanges may provide corroboration. The system must not silently treat one provider as ground truth when sources disagree. Conflict, missing data, incompatible schemas, or ambiguous semantics must fail closed at the relevant validation/intelligence boundary.

## Excluded from this contract

- CoinGlass API;
- CryptoQuant API;
- Glassnode API;
- FRED API;
- commercial whale/news APIs requiring API keys;
- any authenticated exchange/private-account endpoint;
- any invented financial threshold or trading rule.

## Required next engineering work

Define provider-specific contracts/adapters only after public unauthenticated endpoints, timestamps, rate limits, historical availability, and data semantics are verified. Keep raw source ingestion separate from validation, PIT snapshotting, intelligence derivation, and strategy evaluation.
