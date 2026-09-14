"""Immutable, read-only normalized market data models."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Candle:
    """A validated OHLCV candle with an inclusive-open/exclusive-close interval."""

    instrument: str
    interval: str
    opened_at: datetime
    closed_at: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal

    def __post_init__(self) -> None:
        if not self.instrument.strip():
            raise ValueError("instrument must not be empty")
        if not self.interval.strip():
            raise ValueError("interval must not be empty")
        if self.opened_at.tzinfo is None or self.closed_at.tzinfo is None:
            raise ValueError("candle timestamps must be timezone-aware")
        if self.opened_at >= self.closed_at:
            raise ValueError("opened_at must be earlier than closed_at")
        if self.high < max(self.open, self.close, self.low):
            raise ValueError("high must be at least open, close, and low")
        if self.low > min(self.open, self.close, self.high):
            raise ValueError("low must be at most open, close, and high")
        if self.volume < 0:
            raise ValueError("volume must be non-negative")
        if any(value < 0 for value in (self.open, self.high, self.low, self.close)):
            raise ValueError("prices must be non-negative")


__all__ = ["Candle"]
