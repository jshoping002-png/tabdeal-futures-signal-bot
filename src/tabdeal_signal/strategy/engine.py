from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from tabdeal_signal.data.contracts import MarketSnapshot
from tabdeal_signal.data.series import validate_snapshot_series
from tabdeal_signal.domain.contracts import Candle, Direction
from tabdeal_signal.strategy.contracts import StrategyEvaluation, StrategyEvaluationRequest, StrategyEvaluator


@dataclass(frozen=True, slots=True)
class SwingPoint:
    index: int
    price: float
    confirmed_at: datetime


def _confirmed_swings(candles: tuple[Candle, ...], *, high: bool) -> tuple[SwingPoint, ...]:
    points: list[SwingPoint] = []
    for index in range(2, len(candles) - 2):
        value = candles[index].high if high else candles[index].low
        neighbors = tuple(
            candle.high if high else candle.low
            for candle in (candles[index - 2], candles[index - 1], candles[index + 1], candles[index + 2])
        )
        is_swing = value > max(neighbors) if high else value < min(neighbors)
        if is_swing:
            points.append(SwingPoint(index, value, candles[index + 2].close_time))
    return tuple(points)


def _pit_swings(points: tuple[SwingPoint, ...], reference_time: datetime) -> tuple[SwingPoint, ...]:
    return tuple(point for point in points if point.confirmed_at < reference_time)


def _trend(candles: tuple[Candle, ...], reference_time: datetime) -> Direction | None:
    highs = _pit_swings(_confirmed_swings(candles, high=True), reference_time)
    lows = _pit_swings(_confirmed_swings(candles, high=False), reference_time)
    if len(highs) < 2 or len(lows) < 2:
        return None
    h1, h2 = highs[-2:]
    l1, l2 = lows[-2:]
    if h2.price > h1.price and l2.price > l1.price:
        return Direction.LONG
    if h2.price < h1.price and l2.price < l1.price:
        return Direction.SHORT
    return None


def _break_events(candles: tuple[Candle, ...], reference_time: datetime) -> tuple[tuple[datetime, Direction], ...]:
    highs = _confirmed_swings(candles, high=True)
    lows = _confirmed_swings(candles, high=False)
    events: list[tuple[datetime, Direction]] = []
    for index, candle in enumerate(candles):
        if candle.close_time >= reference_time:
            continue
        prior_highs = tuple(p for p in highs if p.index < index and p.confirmed_at < candle.close_time)
        prior_lows = tuple(p for p in lows if p.index < index and p.confirmed_at < candle.close_time)
        if prior_highs and candle.close > prior_highs[-1].price:
            events.append((candle.close_time, Direction.LONG))
        elif prior_lows and candle.close < prior_lows[-1].price:
            events.append((candle.close_time, Direction.SHORT))
    return tuple(events)


def _latest_bos_and_choch(
    candles: tuple[Candle, ...], reference_time: datetime, direction: Direction
):
    events = _break_events(candles, reference_time)
    same_direction = tuple(event for event in events if event[1] is direction)
    if not same_direction:
        return None, None
    latest_bos = same_direction[-1]
    later_opposite = tuple(
        event for event in events if event[0] > latest_bos[0] and event[1] is not direction
    )
    latest_choch = later_opposite[-1] if later_opposite else None
    return latest_bos, latest_choch


class MultiTimeframeStrategyEvaluator(StrategyEvaluator):
    """Strategy Contract V1: 4H trend, 1H BOS/CHOCH, then 15M breakout."""

    def __init__(self, *, symbol: str, direction: Direction) -> None:
        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("symbol is required")
        if not isinstance(direction, Direction):
            raise ValueError("direction must be a Direction")
        self.symbol = symbol
        self.direction = direction

    def evaluate(self, request: StrategyEvaluationRequest) -> StrategyEvaluation:
        if not isinstance(request, StrategyEvaluationRequest):
            raise ValueError("request must be a StrategyEvaluationRequest")
        snapshot = request.snapshot
        reference_time = request.context.reference_time
        series = tuple(snapshot.candles_for(self.symbol, tf) for tf in ("4h", "1h", "15m"))
        if any(not candles for candles in series):
            return StrategyEvaluation(self.direction, False, "INSUFFICIENT_SWING_CONTEXT")
        for timeframe in ("4h", "1h", "15m"):
            report = validate_snapshot_series(snapshot, timeframe)
            if not report.valid:
                return StrategyEvaluation(self.direction, False, report.reason_codes[0])

        candles_4h, candles_1h, candles_15m = series
        trend = _trend(candles_4h, reference_time)
        if trend is not self.direction:
            reason = "TREND_NEUTRAL" if trend is None else ("TREND_LONG_CONFIRMED" if trend is Direction.LONG else "TREND_SHORT_CONFIRMED")
            return StrategyEvaluation(self.direction, False, reason)

        latest_bos, latest_choch = _latest_bos_and_choch(candles_1h, reference_time, self.direction)
        if latest_bos is None:
            return StrategyEvaluation(self.direction, False, "ENTRY_NOT_CONFIRMED")
        if latest_choch is not None:
            reason = "STRUCTURE_CHOCH_LONG_INVALIDATED" if self.direction is Direction.LONG else "STRUCTURE_CHOCH_SHORT_INVALIDATED"
            return StrategyEvaluation(self.direction, False, reason)

        breakout_events = _break_events(candles_15m, reference_time)
        if not any(event[1] is self.direction and event[0] > latest_bos[0] for event in breakout_events):
            return StrategyEvaluation(self.direction, False, "ENTRY_NOT_CONFIRMED")
        reason = "ENTRY_BREAKOUT_LONG" if self.direction is Direction.LONG else "ENTRY_BREAKOUT_SHORT"
        return StrategyEvaluation(self.direction, True, reason
