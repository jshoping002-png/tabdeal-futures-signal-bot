from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from tabdeal_signal.data.contracts import MarketSnapshot, SnapshotRequest


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    detail: str

    def __post_init__(self) -> None:
        if not self.code.strip() or not self.detail.strip():
            raise ValueError("validation issue code and detail are required")


@dataclass(frozen=True, slots=True)
class ValidationReport:
    valid: bool
    issues: tuple[ValidationIssue, ...]

    def __post_init__(self) -> None:
        if self.valid and self.issues:
            raise ValueError("a valid report cannot contain issues")
        if not self.valid and not self.issues:
            raise ValueError("an invalid report must contain at least one issue")


def validate_snapshot(request: SnapshotRequest, snapshot: MarketSnapshot) -> ValidationReport:
    """Validate critical market-data integrity without network or clock access."""
    issues: list[ValidationIssue] = []

    if snapshot.reference_time != request.reference_time:
        issues.append(ValidationIssue("REFERENCE_TIME_MISMATCH", "snapshot reference_time differs from request"))

    requested_pairs = {(symbol, timeframe) for symbol in request.symbols for timeframe in request.timeframes}
    actual_pairs = {(candle.symbol, candle.timeframe) for candle in snapshot.candles}

    for pair in sorted(requested_pairs - actual_pairs):
        issues.append(ValidationIssue("MISSING_DATA", f"missing requested pair: {pair[0]}/{pair[1]}"))

    for pair in sorted(actual_pairs - requested_pairs):
        issues.append(ValidationIssue("UNREQUESTED_DATA", f"snapshot contains unrequested pair: {pair[0]}/{pair[1]}"))

    for candle in snapshot.candles:
        values = (candle.open, candle.high, candle.low, candle.close, candle.volume)
        if not all(isfinite(value) for value in values):
            issues.append(ValidationIssue("NON_FINITE_VALUE", f"non-finite OHLCV for {candle.symbol}/{candle.timeframe}"))
        if min(candle.open, candle.high, candle.low, candle.close) <= 0:
            issues.append(ValidationIssue("NON_POSITIVE_PRICE", f"non-positive price for {candle.symbol}/{candle.timeframe}"))
        if candle.volume < 0:
            issues.append(ValidationIssue("NEGATIVE_VOLUME", f"negative volume for {candle.symbol}/{candle.timeframe}"))
        if not candle.is_available_at(request.reference_time):
            issues.append(ValidationIssue("FUTURE_DATA", f"candle closes after reference_time for {candle.symbol}/{candle.timeframe}"))

    if issues:
        return ValidationReport(False, tuple(issues))
    return ValidationReport(True, ())
