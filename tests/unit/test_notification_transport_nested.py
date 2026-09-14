from tabdeal_signal.notifications.transport import format_signal_notification


def test_signal_formatter_extracts_nested_signal_direction() -> None:
    payload = {
        "status": "SIGNAL",
        "decision": {
            "status": "SIGNAL",
            "signal": {
                "direction": "LONG",
                "signal_id": "signal-1",
            },
        },
        "bot_token": "must-not-be-rendered",
    }

    result = format_signal_notification(payload)

    assert result == "SIGNAL | status=SIGNAL | decision='LONG'"
    assert "signal-1" not in result
    assert "must-not-be-rendered" not in result
