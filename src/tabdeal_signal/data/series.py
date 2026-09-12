from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import re

from tabdeal_signal.data.contracts import MarketSnapshot
from tabdeal_signal.domain.contracts import Candle, UTC


_TIMEFRAME_RE = re.compile(r"^(?P<value>[1-9][0-9]*)(?P<unit>[mhdw])$")


@dataclass(frozen=True, slots=True)
class TimeframeSpec:
    code: str
    duration: timedelta

    @classmethod
    def parse(cls, code: str) -> TimeframeSpec:
        match = _TIMEFRAME_RE.fullmatch(code.strip().lower())
        if match is None:
            raise ValueError("unsupported timeframe; use positive m/h/d/w units")
        value = int(match.group("value"))
        unit = match.group("unit")
        factors = {"m": timedelta(minutes=1), "h": timedelta(hours=1), "d": timedelta(days=1), "w": timedelta(weeks=1)}
        return cls(f"{value}{unit}", factors[unit] * value)


@dataclass(frozen=True, slots=True)
class SeriesIntegrityReport:
    valid: bool
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.valid and self.reason_codes:
            raise ValueError("a valid series report cannot contain reason codes")
        if not self.valid and not self.reason_codes:
            raise ValueError("an invalid series report requires reason codes")


def validate_candle_series(candles: tuple[Candle, ...], timeframe: str) -> SeriesIntegrityReport:
    """Validate duration, ordering, overlap, and continuity without clock/network access."""
    if not candles:
        return SeriesIntegrityReport(False, ("EMPTY_SERIES",))

    try:
        spec = TimeframeSpec.parse(timeframe)
    except ValueError:
        return SeriesIntegrityReport(False, ("INVALID_TIMEFRAME",))

    reasons: list[str] = []
    if any(candle.timeframe != timeframe for candle in candles):
        reasons.append("TIMEFRAME_MISMATCH")
    if tuple(candles) != tuple(sorted(candles, key=lambda candle: candle.open_time)):
        reasons.append("NON_DETERMINISTIC_ORDER")

    for candle in candles:
        if candle.close_time - candle.open_time != spec.duration:
            reasons.append("INVALID_CANDLE_DURATION")
            break

    ordered = tuple(sorted(candles, key=lambda candle: candle.open_time))
    for previous, current in zip(ordered, ordered[1:]):
        if current.open_time < previous.close_time:
            reasons.append("OVERLAPPING_CANDLES")
            break
        if current.open_time != previous.close_time:
            reasons.append("CANDLE_GAP")
            break

    if any(candle.open_time.tzinfo != UTC or candle.close_time.tzinfo != UTC for candle in candles):
        reasons.append("NON_UTC_TIMESTAMP")

    return SeriesIntegrityReport(not reasons, tuple(dict.fromkeys(reasons))) if reasons else SeriesIntegrityReport(True, ())


def validate_snapshot_series(snapshot: MarketSnapshot, timeframe: str) -> SeriesIntegrityReport:
    """Validate every series in a snapshot independently; no LONG/SHORT semantics are involved."""
    symbols = tuple(sorted({candle.symbol for candle in snapshot.candles if candle.timeframe == timeframe}))
    reports = [
        validate_candle_series(snapshot.candles_for(symbol, timeframe), timeframe)
        for symbol in symbols
    ]
    reasons = tuple(dict.fromkeys(code for report in reports for code in report.reason_codes))
    return SeriesIntegrityReport(not reasons, reasons) if reasons else SeriesIntegrityReport(True, ())
