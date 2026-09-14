from tabdeal_signal.notifications.signal_message import format_rich_signal_notification


def test_formatter_accepts_persisted_decision_signal_shape() -> None:
    result = format_rich_signal_notification(
        {
            "status": "SIGNAL",
            "decision": {
                "status": "SIGNAL",
                "signal": {
                    "symbol": "BTCUSDT",
                    "direction": "SHORT",
                    "recommended_leverage": 3,
                    "market_state": "Bearish",
                },
            },
        }
    )

    assert "🔴 SHORT — SELL" in result
    assert "💱 Symbol: BTCUSDT" in result
    assert "⚡ Recommended leverage: 3x" in result
    assert "📉 Market state: Bearish" in result
