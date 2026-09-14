import tabdeal_signal.notifications as notifications
from tabdeal_signal.notifications import (
    NotificationTransport,
    format_rich_signal_notification,
    format_signal_notification,
)
from tabdeal_signal.notifications.signal_message import (
    format_rich_signal_notification as module_rich_formatter,
)
from tabdeal_signal.notifications.transport import (
    NotificationTransport as module_transport,
    format_signal_notification as module_formatter,
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


def test_notification_exports_match_implementation_symbols() -> None:
    assert NotificationTransport is module_transport
    assert format_signal_notification is module_formatter
    assert format_rich_signal_notification is module_rich_formatter


def test_notification_all_declares_only_supported_public_symbols() -> None:
    assert notifications.__all__ == [
        "NotificationTransport",
        "format_rich_signal_notification",
        "format_signal_notification",
    ]
