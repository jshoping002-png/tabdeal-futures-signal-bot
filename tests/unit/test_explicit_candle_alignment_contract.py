from datetime import datetime, timedelta

from tabdeal_signal.data.alignment import align_latest_closed_candle
from tabdeal_signal.domain.contracts import Candle, UTC


def make_candle(open_time: datetime, timeframe: str = "1h") -> Candle:
    return Candle(
        symbol="BTCUSDT",
        timeframe=timeframe,
        open_time=open_time,
        close_time=open_time + timedelta(hours=1),
        open=100.0,
        high=110.0,
        low=90.0,
        close=105.0,
        volume=1.0,
    )


def test_alignment_selects_unique_latest_strictly_closed_candle():
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    candles = (make_candle(t0), make_candle(t0 + timedelta(hours=1)), make_candle(t0 + timedelta(hours=2)))
    result = align_latest_closed_candle(candles, "1h", t0 + timedelta(hours=3, minutes=1), t0)
    assert result.candle == candles[2]
    assert result.reason_codes == ()


def test_alignment_blocks_when_no_candle_is_strictly_closed():
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    result = align_latest_closed_candle((make_candle(t0),), "1h", t0 + timedelta(hours=1), t0)
    assert result.candle is None
    assert result.reason_codes == ("NO_CLOSED_CANDLE",)


def test_alignment_blocks_timeframe_mismatch():
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    result = align_latest_closed_candle((make_candle(t0),), "4h", t0 + timedelta(hours=2), t0)
    assert result.candle is None
    assert result.reason_codes == ("TIMEFRAME_MISMATCH",)


def test_alignment_blocks_invalid_series_before_selection():
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    candles = (make_candle(t0), make_candle(t0 + timedelta(hours=2)))
    result = align_latest_closed_candle(candles, "1h", t0 + timedelta(hours=4), t0)
    assert result.candle is None
    assert "CANDLE_GAP" in result.reason_codes


def test_alignment_is_deterministic():
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    candles = (make_candle(t0), make_candle(t0 + timedelta(hours=1)))
    first = align_latest_closed_candle(candles, "1h", t0 + timedelta(hours=2, minutes=1), t0)
    second = align_latest_closed_candle(candles, "1h", t0 + timedelta(hours=2, minutes=1), t0)
    assert first == second
