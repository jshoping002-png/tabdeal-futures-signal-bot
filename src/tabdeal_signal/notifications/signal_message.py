"""Rich, text-only Telegram formatting for LONG and SHORT signal notifications."""

from __future__ import annotations

from collections.abc import Mapping


def _value(payload: Mapping[str, object], *keys: str) -> object:
    current: object = payload
    for key in keys:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current


def _line(label: str, value: object) -> str:
    return f"{label}: {value if value is not None else 'N/A'}"


def format_rich_signal_notification(payload: Mapping[str, object]) -> str:
    """Format a deterministic Telegram message without secrets or trade execution.

    The formatter accepts either flat fields or fields nested under ``signal``.
    Missing optional values are rendered as ``N/A`` rather than fabricated.
    """
    signal = payload.get("signal")
    source: Mapping[str, object] = signal if isinstance(signal, Mapping) else payload
    direction = str(source.get("direction", "UNKNOWN")).upper()
    is_long = direction in {"LONG", "BUY"}
    marker = "🟢 LONG — BUY" if is_long else "🔴 SHORT — SELL" if direction in {"SHORT", "SELL"} else f"⚪ {direction}"
    market_icon = "📈" if is_long else "📉" if direction in {"SHORT", "SELL"} else "📊"

    leverage = source.get("recommended_leverage", source.get("leverage"))
    unlevered = source.get("estimated_return_pct", source.get("return_pct"))
    levered = source.get("estimated_leveraged_return_pct")
    risk = source.get("risk_level")
    market = source.get("market_state", source.get("market_trend"))

    lines = [
        "📡 FUTURES SIGNAL",
        f"{marker}",
        _line("💱 Symbol", source.get("symbol")),
        _line("🏦 Exchange", source.get("exchange")),
        _line("📄 Contract", source.get("contract_type", "Perpetual")),
        _line("⚡ Recommended leverage", f"{leverage}x" if leverage is not None else None),
        _line("⚠️ Risk", risk),
        _line(f"{market_icon} Market state", market),
        _line("🎯 Entry", source.get("entry", source.get("entry_price"))),
        _line("🛑 Stop loss", source.get("stop_loss", source.get("stop_loss_price"))),
        _line("📉 Loss before leverage", source.get("estimated_loss_pct")),
        _line("💰 Estimated return before leverage", unlevered),
        _line("🚀 Estimated return after leverage", levered),
        _line("⚖️ Risk/Reward", source.get("risk_reward")),
        "",
        "🎯 Take-profit targets",
        _line("🥇 TP1", source.get("tp1")),
        _line("🥈 TP2", source.get("tp2")),
        _line("🥉 TP3", source.get("tp3")),
        "",
        "📊 Technical confirmations",
        _line("• RSI", source.get("rsi")),
        _line("• EMA", source.get("ema")),
        _line("• MACD", source.get("macd")),
        _line("• Volume", source.get("volume")),
        _line("• Order-book imbalance", source.get("order_book_imbalance")),
        "",
        "⚠️ Not financial advice. Returns are estimates, not guarantees.",
        "🛡️ Risk management is mandatory. No order execution is performed.",
    ]
    return "\n".join(lines)
