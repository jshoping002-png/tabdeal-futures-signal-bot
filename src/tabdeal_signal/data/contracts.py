from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from tabdeal_signal.domain.contracts import Candle, UTC


@dataclass(frozen=True, slots=True)
class SnapshotRequest:
    symbols: tuple[str, ...]
    timeframes: tuple[str, ...]
    reference_time: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.symbols, tuple) or not isinstance(self.timeframes, tuple):
            raise ValueError("symbols and timeframes must be tuples")
        if any(not isinstance(symbol, str) for symbol in self.symbols):
            raise ValueError("symbols must contain only strings")
        if not self.symbols or any(not symbol.strip() for symbol in self.symbols):
            raise ValueError("symbols must contain at least one non-empty symbol")
        if len(set(self.symbols)) != len(self.symbols):
            raise ValueError("symbols must not contain duplicates")
        if any(not isinstance(timeframe, str) for timeframe in self.timeframes):
            raise ValueError("timeframes must contain only strings")
        if not self.timeframes or any(not timeframe.strip() for timeframe in self.timeframes):
            raise ValueError("timeframes must contain at least one non-empty timeframe")
        if len(set(self.timeframes)) != len(self.timeframes):
            raise ValueError("timeframes must not contain duplicates")
        if self.reference_time.tzinfo is None or self.reference_time.tzinfo != UTC:
            raise ValueError("reference_time must be UTC")


@dataclass(frozen=True, slots=True)
class MarketSnapshot:
    snapshot_id: str
    source_id: str
    reference_time: datetime
    candles: tuple[Candle, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.candles, tuple):
            raise ValueError("candles must be a tuple")
        if not self.candles or any(not isinstance(candle, Candle) for candle in self.candles):
            raise ValueError("candles must contain Candle instances")
        if not self.snapshot_id.strip():
            raise ValueError("snapshot_id is required")
        if not self.source_id.strip():
            raise ValueError("source_id is required")
        if self.reference_time.tzinfo is None or self.reference_time.tzinfo != UTC:
            raise ValueError("reference_time must be UTC")
        if not self.candles:
            raise ValueError("snapshot must contain at least one candle")

        keys = [(c.symbol, c.timeframe, c.open_time) for c in self.candles]
        if len(set(keys)) != len(keys):
            raise ValueError("snapshot contains duplicate candles")
        if keys != sorted(keys):
            raise ValueError("candles must be in deterministic order")
        if any(not candle.is_available_at(self.reference_time) for candle in self.candles):
            raise ValueError("snapshot contains data unavailable at reference_time")

    def candles_for(self, symbol: str, timeframe: str) -> tuple[Candle, ...]:
        return tuple(
            candle
            for candle in self.candles
            if candle.symbol == symbol and candle.timeframe == timeframe
        )


class MarketDataSource(Protocol):
    """Point-in-time source contract; implementations must fail closed on invalid data."""

    source_id: str

    def snapshot(self, request: SnapshotRequest) -> MarketSnapshot:
        """Return only data available at request.reference_time."""
        ...
