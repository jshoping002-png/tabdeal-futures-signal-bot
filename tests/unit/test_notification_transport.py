from tabdeal_signal.notifications.transport import format_signal_notification


def test_signal_formatter_is_deterministic_and_secret_free() -> None:
    payload = {"status": "SIGNAL", "decision": "LONG", "bot_token": "must-not-be-rendered"}

    result = format_signal_notification(payload)

    assert result == "SIGNAL | status=SIGNAL | decision='LONG'"
    assert "must-not-be-rendered" not in result
