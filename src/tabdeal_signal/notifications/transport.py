"""Notification transport contracts for signal outbox delivery only."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol


class NotificationTransport(Protocol):
    """Transport boundary; implementations must not execute trades or orders."""

    def send(self, *, event_id: str, payload: Mapping[str, object]) -> None:
        """Deliver one signal notification or raise an exception."""


def format_signal_notification(payload: Mapping[str, object]) -> str:
    """Create a deterministic, secret-free text representation of a signal payload."""
    decision = payload.get("decision")
    status = payload.get("status", "SIGNAL")
    return f"SIGNAL | status={status} | decision={decision!r}"
