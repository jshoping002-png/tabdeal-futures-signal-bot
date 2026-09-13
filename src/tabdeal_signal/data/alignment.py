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
        if not isinstance(self.timeframe, TimeframeSpec):
            raise ValueError("timeframe must be a TimeframeSpec")
        if not isinstance(self.anchor_time, datetime):
            raise ValueError("anchor_time must be a datetime")
        if self.anchor_time.tzinfo is None or self.anchor_time.tzinfo != UTC:
            raise ValueError("anchor_time must be UTC")

    def contains(self, candle: Candle) -> bool:
        if not isinstance(candle, Candle):
            raise ValueError("candle must be a Candle")
        if candle.timeframe != self.timeframe.code:
            return False
        elapsed = candle.open_time - self.anchor_time
        if elapsed < timedelta(0):
            return False
        return elapsed % self.timeframe.duration == timedelta(0)


def select_closed_candles(
    candles: tuple[Candle, ...],
    reference_time: datetime,
) -> tuple[Candle, ...]:
    """Select only candles whose close time is strictly before the reference time."""
    if not isinstance(candles, tuple):
        raise ValueError("candles must be a tuple")
    if any(not isinstance(candle, Candle) for candle in candles):
        raise ValueError("candles must contain Candle instances")
    if not isinstance(reference_time, datetime):
        raise ValueError("reference_time must be a datetime")
    if reference_time.tzinfo is None or reference_time.tzinfo != UTC:
        raise ValueError("reference_time must be UTC")
    return tuple(candle for candle in candles if candle.close_time < reference_time)


def validate_alignment(candles: tuple[Candle, ...], policy: AlignmentPolicy) -> tuple[str, ...]:
    """Return deterministic alignment reason codes without inferring boundaries."""
    if not isinstance(candles, tuple):
        raise ValueError("candles must be a tuple")
    if any(not isinstance(candle, Candle) for candle in candles):
        raise ValueError("candles must contain Candle instances")
    if not isinstance(policy, AlignmentPolicy):
        raise ValueError("policy must be an AlignmentPolicy")
    if not candles:
        return ("EMPTY_SERIES",)

    has_non_utc_timestamp = False
    has_boundary_mismatch = False

    for candle in candles:
        if candle.open_time.tzinfo != UTC or candle.close_time.tzinfo != UTC:
            has_non_utc_timestamp = True
        if not policy.contains(candle):
            has_boundary_mismatch = True

    reasons: list[str] = []
    if has_non_utc_timestamp:
        reasons.append("NON_UTC_TIMESTAMP")
    if has_boundary_mismatch:
        reasons.append("CANDLE_BOUNDARY_MISMATCH")
    return tuple(reasons)
