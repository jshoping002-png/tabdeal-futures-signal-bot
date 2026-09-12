from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from tabdeal_signal.data.series import TimeframeSpec
from tabdeal_signal.domain.contracts import Candle, UTC


@dataclass(frozen=True, slots=True)
class AlignmentPolicy:
    """Explicit candle-boundary policy; no exchange/session anchor is inferred."""

    timeframe: TimeframeSpec
    anchor_time: datetime

    def __post_init__(self) -> None:
        if self.anchor_time.tzinfo is None or self.anchor_time.tzinfo != UTC:
            raise ValueError("anchor_time must be UTC")

    def contains(self, candle: Candle) -> bool:
        if candle.timeframe != self.timeframe.code:
            return False
        elapsed = candle.open_time - self.anchor_time
        if elapsed < timedelta(0):
            return False
        return elapsed % self.timeframe.duration == timedelta(0)


def validate_alignment(candles: tuple[Candle, ...], policy: AlignmentPolicy) -> tuple[str, ...]:
    """Return stable reason codes for candles that violate an explicit boundary policy."""
    reasons: list[str] = []
    for candle in candles:
        if candle.open_time.tzinfo != UTC or candle.close_time.tzinfo != UTC:
            reasons.append("NON_UTC_TIMESTAMP")
        if not policy.contains(candle):
            reasons.append("CANDLE_BOUNDARY_MISMATCH")
    return tuple(dict.fromkeys(reasons))
