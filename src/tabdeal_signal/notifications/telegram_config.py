from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TelegramNotificationSettings:
    """Validated configuration for signal notifications via Telegram.

    This object contains configuration only. It does not send messages, place
    orders, or interact with an exchange.
    """

    bot_token: str
    chat_id: str
    enabled: bool = False
    timeout_seconds: float = 10.0
    max_attempts: int = 3

    def __post_init__(self) -> None:
        if not isinstance(self.bot_token, str) or not self.bot_token.strip():
            raise ValueError("bot_token is required")
        if any(character.isspace() for character in self.bot_token):
            raise ValueError("bot_token must not contain whitespace")
        if not isinstance(self.chat_id, str) or not self.chat_id.strip():
            raise ValueError("chat_id is required")
        if not isinstance(self.enabled, bool):
            raise ValueError("enabled must be a bool")
        if isinstance(self.timeout_seconds, bool) or self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if isinstance(self.max_attempts, bool) or not isinstance(self.max_attempts, int):
            raise ValueError("max_attempts must be an integer")
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")

    @classmethod
    def from_env(cls, environ: dict[str, str] | None = None) -> "TelegramNotificationSettings":
        """Build settings from environment variables without logging secrets."""

        env = os.environ if environ is None else environ
        enabled_raw = env.get("TELEGRAM_ENABLED", "false").strip().lower()
        if enabled_raw not in {"true", "false", "1", "0", "yes", "no"}:
            raise ValueError("TELEGRAM_ENABLED must be a boolean value")

        return cls(
            bot_token=env.get("TELEGRAM_BOT_TOKEN", ""),
            chat_id=env.get("TELEGRAM_CHAT_ID", ""),
            enabled=enabled_raw in {"true", "1", "yes"},
            timeout_seconds=float(env.get("TELEGRAM_TIMEOUT_SECONDS", "10")),
            max_attempts=int(env.get("TELEGRAM_MAX_ATTEMPTS", "3")),
        )

    def redacted(self) -> dict[str, object]:
        """Return safe diagnostics that never expose the bot token."""

        return {
            "bot_token_configured": bool(self.bot_token),
            "chat_id": self.chat_id,
            "enabled": self.enabled,
            "timeout_seconds": self.timeout_seconds,
            "max_attempts": self.max_attempts,
        }
