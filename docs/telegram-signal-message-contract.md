# Telegram Signal Message Contract

This contract defines the text-only Telegram format for both `LONG` and `SHORT` futures signals.

## Required sections

Every signal message should include:

1. Header: `📡 FUTURES SIGNAL`, source, date, and time.
2. Market identity: symbol, exchange, contract type, and direction.
3. Suggested leverage: `⚡` leverage value and an explicit `Recommended` label.
4. Risk: `⚠️` risk level and a short explanation.
5. Market state: trend, momentum, volume, and relevant timeframe confirmations.
6. Entry: `🎯` approximate entry price or entry range.
7. Stop loss: `🛑` stop-loss price and estimated unleveraged loss percentage.
8. Take-profit targets: `🥇 TP1`, `🥈 TP2`, and `🥉 TP3`, each with price and estimated unleveraged return.
9. Leveraged estimates: approximate return for each target after applying the suggested leverage.
10. Risk/reward: `⚖️` ratio for each target.
11. Technical analysis: indicators such as RSI, EMA, MACD, and order-book imbalance when available.
12. Confirmations: timeframe trends and indicator confirmations.
13. Safety footer: this is not financial advice; returns are not guaranteed; risk management is required.

## Direction-specific rules

### LONG / BUY

- Direction marker: `🟢 LONG — BUY`
- Market bias is normally represented with `📈` when bullish.
- Take-profit prices must be above the entry price.
- Stop-loss price must be below the entry price.

### SHORT / SELL

- Direction marker: `🔴 SHORT — SELL`
- Market bias is normally represented with `📉` when bearish.
- Take-profit prices must be below the entry price.
- Stop-loss price must be above the entry price.

## Return calculations

- Unleveraged target return is calculated from the entry price to the target price in the signal direction.
- Leveraged return is an estimate based on the unleveraged return multiplied by the suggested leverage.
- Fees, funding, slippage, liquidation distance, and execution differences must be disclosed or accounted for when supported by the data.
- If a value is unavailable, the message must use an explicit unavailable marker rather than inventing a number.

## Safety boundary

The message is informational and notification-only. This contract must not add order execution, trade placement, exchange order endpoints, or automated trading behavior.
