from datetime import datetime, timedelta, timezone

from tabdeal_signal.data.series import TimeframeSpec, validate_candle_series, validate_snapshot_series
from tabdeal_signal.data.contracts import MarketSnapshot
from tabdeal_signal.domain.contracts import Candle

UTC = timezone.utc


def candle(hour: int, timeframe: str = "1h") -> Candle:
    start = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(hours=hour)
    return Candle("BTCUSDT", timeframe, start, start + timedelta(hours=1), 100, 110, 90, 105, 1)


def test_timeframe_parser_is_explicit_and_deterministic() -> None:
    assert TimeframeSpec.parse("4h").duration == timedelta(hours=4)
    assert TimeframeSpec.parse("1d").duration == timedelta(days=1)


def test_unsupported_month_unit_is_rejected() -> None:
    try:
        TimeframeSpec.parse("1M")
    except ValueError as exc:
        assert "unsupported timeframe" in str(exc)
    else:
        raise AssertionError("calendar months must not be guessed as fixed durations")


def test_contiguous_series_passes() -> None:
    report = validate_candle_series((candle(0), candle(1), candle(2)), "1h")
    assert report.valid is True


def test_gap_blocks_series() -> None:
    report = validate_candle_series((candle(0), candle(2)), "1h")
    assert report.valid is False
    assert "CANDLE_GAP" in report.reason_codes


def test_overlap_blocks_series() -> None:
    first = candle(0)
    overlapping = Candle("BTCUSDT", "1h", first.open_time + timedelta(minutes=30), first.close_time + timedelta(minutes=30), 100, 110, 90, 105, 1)
    report = validate_candle_series((first, overlapping), "1h")
    assert report.valid is False
    assert "OVERLAPPING_CANDLES" in report.reason_codes


def test_wrong_duration_blocks_series() -> None:
    first = candle(0)
    second = Candle("BTCUSDT", "1h", first.close_time, first.close_time + timedelta(hours=2), 100, 110, 90, 105, 1)
    report = validate_candle_series((first, second), "1h")
    assert report.valid is False
    assert "INVALID_CANDLE_DURATION" in report.reason_codes


def test_wrong_order_blocks_series() -> None:
    report = validate_candle_series((candle(1), candle(0)), "1h")
    assert report.valid is False
    assert "NON_DETERMINISTIC_ORDER" in report.reason_codes


def test_snapshot_series_are_checked_independently() -> None:
    ref = candle(2).close_time + timedelta(microseconds=1)
    snap = MarketSnapshot("snap-1", "source-a", ref, (candle(0), candle(1), candle(2)))
    report = validate_snapshot_series(snap, "1h")
    assert report.valid is True


def test_snapshot_series_with_gap_blocks() -> None:
    ref = candle(3).close_time + timedelta(microseconds=1)
    snap = MarketSnapshot("snap-1", "source-a", ref, (candle(0), candle(2), candle(3)))
    report = validate_snapshot_series(snap, "1h")
    assert report.valid is False
    assert "CANDLE_GAP" in report.reason_codes
