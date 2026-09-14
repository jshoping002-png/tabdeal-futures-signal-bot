"""Notification transport contracts for signal outbox delivery only."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol


class NotificationTransport(Protocol):
    """Transport boundary; implementations must not execute trades or orders."""

    def send(self, *, event_id: str, payload: Mapping[str, object]) -> None:
        """Deliver one signal notification or raise an exception."""


def format_signal_notification(payload: Mapping[str, object]) -> str:
    """Create a deterministic, secret-free text representation of a signal payload.

    Persistence payloads contain the final decision under ``decision`` and, for
    signal outcomes, the selected signal under ``decision.signal``. A flat
    ``decision`` value remains supported for compatibility with older payloads.
    """
    status = payload.get("status", "SIGNAL")
    decision = payload.get("decision")

    if isinstance(decision, Mapping):
        signal = decision.get("signal")
        if isinstance(signal, Mapping):
            direction = signal.get("direction")
            if direction is not None:
                decision_text = repr(direction)
            else:
                decision_text = repr(signal)
        else:
            decision_text = repr(decision)
    else:
        decision_text = repr(decision)

    return f"SIGNAL | status={status} | decision={decision_text}"
