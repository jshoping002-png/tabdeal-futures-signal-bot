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


def test_long_signal_uses_long_markers_without_rewriting_levels() -> None:
    result = format_rich_signal_notification(
        {
            "signal": {
                "symbol": "ETHUSDT",
                "direction": "LONG",
                "entry": 2000,
                "stop_loss": 1900,
                "take_profit_1": 2100,
                "take_profit_2": 2200,
                "take_profit_3": 2300,
            }
        }
    )

    assert "🟢 LONG — BUY" in result
    assert "📈 Market state:" in result
    assert "🎯 Entry: 2000" in result
    assert "🛑 Stop loss: 1900" in result
    assert "TP1: 2100" in result
    assert "TP2: 2200" in result
    assert "TP3: 2300" in result


def test_short_signal_uses_short_markers_without_rewriting_levels() -> None:
    result = format_rich_signal_notification(
        {
            "signal": {
                "symbol": "ETHUSDT",
                "direction": "SHORT",
                "entry": 2000,
                "stop_loss": 2100,
                "take_profit_1": 1900,
                "take_profit_2": 1800,
                "take_profit_3": 1700,
            }
        }
    )

    assert "🔴 SHORT — SELL" in result
    assert "📉 Market state:" in result
    assert "🎯 Entry: 2000" in result
    assert "🛑 Stop loss: 2100" in result
    assert "TP1: 1900" in result
    assert "TP2: 1800" in result
    assert "TP3: 1700" in result
