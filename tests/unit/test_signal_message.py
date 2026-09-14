from tabdeal_signal.notifications.signal_message import format_rich_signal_notification


def test_long_message_contains_required_sections_and_emojis() -> None:
    result = format_rich_signal_notification(
        {
            "symbol": "BTCUSDT",
            "exchange": "Binance Futures",
            "direction": "LONG",
            "recommended_leverage": 5,
            "risk_level": "LOW",
            "market_trend": "Bullish",
            "entry_price": 100,
            "stop_loss_price": 98,
            "estimated_loss_pct": "-2%",
            "estimated_return_pct": "+4%",
            "estimated_leveraged_return_pct": "+20%",
            "risk_reward": "1:2",
            "tp1": "102 (+2%, 10% leveraged)",
            "tp2": "104 (+4%, 20% leveraged)",
            "tp3": "106 (+6%, 30% leveraged)",
            "rsi": 58,
        }
    )

    assert "🟢 LONG — BUY" in result
    assert "⚡ Recommended leverage: 5x" in result
    assert "💰 Estimated return before leverage: +4%" in result
    assert "🚀 Estimated return after leverage: +20%" in result
    assert "🛑 Stop loss: 98" in result
    assert "🎯 Take-profit targets" in result
    assert "⚠️ Not financial advice" in result


def test_short_message_uses_short_direction_and_market_icon() -> None:
    result = format_rich_signal_notification(
        {"symbol": "ETHUSDT", "direction": "SHORT", "market_state": "Bearish"}
    )

    assert "🔴 SHORT — SELL" in result
    assert "📉 Market state: Bearish" in result
    assert "🎯 Entry: N/A" in result
    assert "🛡️ Risk management is mandatory" in result
