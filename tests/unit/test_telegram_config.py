import pytest

from tabdeal_signal.notifications.telegram_config import TelegramNotificationSettings


def test_settings_validate_and_redact_token() -> None:
    settings = TelegramNotificationSettings(
        bot_token="123456:secret-token",
        chat_id="-100123",
        enabled=True,
    )

    diagnostics = settings.redacted()
    assert diagnostics["bot_token_configured"] is True
    assert "secret-token" not in str(diagnostics)
    assert diagnostics["chat_id"] == "-100123"


def test_settings_load_from_environment() -> None:
    settings = TelegramNotificationSettings.from_env(
        {
            "TELEGRAM_BOT_TOKEN": "123:token",
            "TELEGRAM_CHAT_ID": "42",
            "TELEGRAM_ENABLED": "yes",
            "TELEGRAM_TIMEOUT_SECONDS": "4.5",
            "TELEGRAM_MAX_ATTEMPTS": "5",
        }
    )

    assert settings.enabled is True
    assert settings.timeout_seconds == 4.5
    assert settings.max_attempts == 5


@pytest.mark.parametrize(
    "kwargs",
    [
        {"bot_token": "", "chat_id": "42"},
        {"bot_token": "123:token", "chat_id": ""},
        {"bot_token": "123 token", "chat_id": "42"},
        {"bot_token": "123:token", "chat_id": "42", "timeout_seconds": 0},
        {"bot_token": "123:token", "chat_id": "42", "max_attempts": 0},
    ],
)
def test_invalid_settings_are_rejected(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        TelegramNotificationSettings(**kwargs)


def test_invalid_enabled_environment_value_is_rejected() -> None:
    with pytest.raises(ValueError):
        TelegramNotificationSettings.from_env(
            {
                "TELEGRAM_BOT_TOKEN": "123:token",
                "TELEGRAM_CHAT_ID": "42",
                "TELEGRAM_ENABLED": "sometimes",
            }
        )
