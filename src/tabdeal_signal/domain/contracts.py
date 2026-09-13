from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from math import isfinite
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
        if not isinstance(self.symbol, str):
            raise ValueError("symbol must be a string")
        if not isinstance(self.timeframe, str):
            raise ValueError("timeframe must be a string")
        if not self.symbol.strip():
            raise ValueError("symbol must not be empty")
        if not self.timeframe.strip():
            raise ValueError("timeframe must not be empty")
        if self.close_time.tzinfo is None or self.open_time.tzinfo is None:
            raise ValueError("candle timestamps must be timezone-aware")
        if self.open_time.tzinfo != UTC or self.close_time.tzinfo != UTC:
            raise ValueError("candle timestamps must be UTC")
        if self.close_time <= self.open_time:
            raise ValueError("close_time must be after open_time")
        if not isinstance(self.open, (int, float)) or isinstance(self.open, bool):
            raise ValueError("open must be numeric")
        if not isinstance(self.high, (int, float)) or isinstance(self.high, bool):
            raise ValueError("high must be numeric")
        if not isinstance(self.low, (int, float)) or isinstance(self.low, bool):
            raise ValueError("low must be numeric")
        if not isinstance(self.close, (int, float)) or isinstance(self.close, bool):
            raise ValueError("close must be numeric")
        if not isinstance(self.volume, (int, float)) or isinstance(self.volume, bool):
            raise ValueError("volume must be numeric")
        if not all(isfinite(value) for value in (self.open, self.high, self.low, self.close, self.volume)):
            raise ValueError("candle numeric values must be finite")
        if self.high < max(self.open, self.close) or self.low > min(self.open, self.close):
            raise ValueError("invalid OHLC bounds")
        if self.low > self.high:
            raise ValueError("low must not exceed high")
        if self.volume < 0:
            raise ValueError("volume must not be negative")

    def is_available_at(self, reference_time: datetime) -> bool:
        """Return True only when the candle closed strictly before reference_time."""
        if reference_time.tzinfo is None or reference_time.tzinfo != UTC:
            raise ValueError("reference_time must be UTC")
        return self.close_time < reference_time


@dataclass(frozen=True, slots=True)
class DecisionContext:
    decision_time: datetime
    reference_time: datetime
    snapshot_id: str
    config_version: str

    def __post_init__(self) -> None:
        if not isinstance(self.decision_time, datetime):
            raise ValueError("decision_time must be a datetime")
        if not isinstance(self.reference_time, datetime):
            raise ValueError("reference_time must be a datetime")
        for value in (self.decision_time, self.reference_time):
            if value.tzinfo is None or value.tzinfo != UTC:
                raise ValueError("decision timestamps must be UTC")
        if not isinstance(self.snapshot_id, str) or not isinstance(self.config_version, str):
            raise ValueError("snapshot_id and config_version must be strings")
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
        if not isinstance(self.direction, Direction):
            raise ValueError("direction must be a Direction")
        if not isinstance(self.status, DecisionStatus):
            raise ValueError("status must be a DecisionStatus")
        if not isinstance(self.reason_code, str):
            raise ValueError("reason_code must be a string")
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
        if not isinstance(self.signal_id, str):
            raise ValueError("signal_id must be a string")
        if not self.signal_id.strip():
            raise ValueError("signal_id is required")
        if not isinstance(self.direction, Direction):
            raise ValueError("direction must be a Direction")
        if not isinstance(self.created_at, datetime):
            raise ValueError("created_at must be a datetime")
        if self.created_at.tzinfo is None or self.created_at.tzinfo != UTC:
            raise ValueError("created_at must be UTC")
        if not isinstance(self.snapshot_id, str):
            raise ValueError("snapshot_id must be a string")
        if not self.snapshot_id.strip():
            raise ValueError("snapshot_id is required")
        if not isinstance(self.config_version, str):
            raise ValueError("config_version must be a string")
        if not self.config_version.strip():
            raise ValueError("config_version is required")
        if not isinstance(self.reason_code, str):
            raise ValueError("reason_code must be a string")
        if not self.reason_code.strip():
            raise ValueError("reason_code is required")
