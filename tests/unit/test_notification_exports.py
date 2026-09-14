from tabdeal_signal.notifications import (
    NotificationTransport,
    format_rich_signal_notification,
    format_signal_notification,
)


def test_notification_public_exports_are_importable() -> None:
    assert NotificationTransport is not None
    assert callable(format_signal_notification)
    assert callable(format_rich_signal_notification)


def test_notification_exports_preserve_formatter_boundaries() -> None:
    payload = {"status": "SIGNAL", "decision": {"signal": {"direction": "LONG"}}}

    simple = format_signal_notification(payload)
    rich = format_rich_signal_notification(payload)

    assert simple.startswith("SIGNAL | status=SIGNAL | decision=")
    assert "🟢 LONG — BUY" in rich
    assert "No order execution is performed." in rich
