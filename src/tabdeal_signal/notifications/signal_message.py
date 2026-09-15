"""Rich, text-only Telegram formatting for LONG and SHORT signal notifications."""

from __future__ import annotations

from collections.abc import Mapping


def _line(label: str, value: object) -> str:
    return f"{label}: {value if value is not None else 'N/A'}"


def _format_leverage(value: object) -> object:
    """Render leverage consistently without producing values such as ``3xx``."""
    if value is None:
        return None
    if isinstance(value, str) and value.strip().lower().endswith("x"):
        return value.strip()
    return f"{value}x"


def format_rich_signal_notification(payload: Mapping[str, object]) -> str:
    """Format a deterministic Telegram message without secrets or trade execution.

    The formatter accepts flat fields, fields nested under ``signal``, or the
    persistence shape ``decision.signal``. Missing values become ``N/A``.
    """
    candidate = payload.get("signal")
    if not isinstance(candidate, Mapping):
        decision = payload.get("decision")
        candidate = decision.get("signal") if isinstance(decision, Mapping) else None
    source: Mapping[str, object] = candidate if isinstance(candidate, Mapping) else payload

    direction = str(source.get("direction", "UNKNOWN")).upper()
    is_long = direction in {"LONG", "BUY"}
    is_short = direction in {"SHORT", "SELL"}
    marker = "🟢 LONG — BUY" if is_long else "🔴 SHORT — SELL" if is_short else f"⚪ {direction}"
    market_icon = "📈" if is_long else "📉" if is_short else "📊"

    leverage = source.get("recommended_leverage", source.get("leverage"))
    unlevered = source.get("estimated_return_pct", source.get("return_pct"))
    levered = source.get("estimated_leveraged_return_pct")
    risk = source.get("risk_level")
    market = source.get("market_state", source.get("market_trend"))

    lines = [
        "📡 FUTURES SIGNAL",
        marker,
        _line("💱 Symbol", source.get("symbol")),
        _line("🏦 Exchange", source.get("exchange")),
        _line("📄 Contract", source.get("contract_type", "Perpetual")),
        _line("⚡ Recommended leverage", _format_leverage(leverage)),
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
        _line("🥇 TP1", source.get("tp1", source.get("take_profit_1"))),
        _line("🥈 TP2", source.get("tp2", source.get("take_profit_2"))),
        _line("🥉 TP3", source.get("tp3", source.get("take_profit_3"))),
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