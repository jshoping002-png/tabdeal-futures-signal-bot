from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Final


UTC: Final = timezone.utc


class Direction(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class DecisionStatus(str, Enum):
    SIGNAL = "SIGNAL"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class Candle:
    symbol: str
    timeframe: str
    open_time: datetime
    close_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

    def __post_init__(self) -> None:
        if not self.symbol.strip():
            raise ValueError("symbol must not be empty")
        if self.close_time.tzinfo is None or self.open_time.tzinfo is None:
            raise ValueError("candle timestamps must be timezone-aware")
        if self.open_time.tzinfo != UTC or self.close_time.tzinfo != UTC:
            raise ValueError("candle timestamps must be UTC")
        if self.close_time <= self.open_time:
            raise ValueError("close_time must be after open_time")
        if self.high < max(self.open, self.close) or self.low > min(self.open, self.close):
            raise ValueError("invalid OHLC bounds")
        if self.low > self.high:
            raise ValueError("low must not exceed high")
        if self.volume < 0:
            raise ValueError("volume must not be negative")


@dataclass(frozen=True, slots=True)
class DecisionContext:
    decision_time: datetime
    reference_time: datetime
    snapshot_id: str
    config_version: str

    def __post_init__(self) -> None:
        for value in (self.decision_time, self.reference_time):
            if value.tzinfo is None or value.tzinfo != UTC:
                raise ValueError("decision timestamps must be UTC")
        if not self.snapshot_id.strip() or not self.config_version.strip():
            raise ValueError("snapshot_id and config_version are required")
        if self.reference_time > self.decision_time:
            raise ValueError("reference_time cannot be after decision_time")


@dataclass(frozen=True, slots=True)
class SideDecision:
    direction: Direction
    status: DecisionStatus
    reason_code: str

    def __post_init__(self) -> None:
        if not self.reason_code.strip():
            raise ValueError("reason_code is required")


@dataclass(frozen=True, slots=True)
class SignalDecision:
    signal_id: str
    direction: Direction
    created_at: datetime
    snapshot_id: str
    config_version: str
    reason_code: str

    def __post_init__(self) -> None:
        if not self.signal_id.strip():
            raise ValueError("signal_id is required")
        if self.created_at.tzinfo is None or self.created_at.tzinfo != UTC:
            raise ValueError("created_at must be UTC")
        if not self.snapshot_id.strip() or not self.config_version.strip():
            raise ValueError("snapshot_id and config_version are required")
        if not self.reason_code.strip():
            raise ValueError("reason_code is required")
