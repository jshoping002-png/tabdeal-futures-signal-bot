from datetime import datetime, timedelta

import pytest

from tabdeal_signal.data.series import validate_candle_series
from tabdeal_signal.domain.contracts import Candle, UTC


def candle(open_time: datetime, *, timeframe: str = "1h") -> Candle:
    close_time = open_time + timedelta(hours=1)
    return Candle(
        symbol="BTCUSDT",
        timeframe=timeframe,
        open_time=open_time,
        close_time=close_time,
        open=100.0,
        high=110.0,
        low=90.0,
        close=105.0,
        volume=1.0,
    )


def test_empty_series_is_invalid():
    assert validate_candle_series((), "1h").reason_codes == ("EMPTY_SERIES",)


def test_unsorted_series_is_invalid_not_repaired():
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    report = validate_candle_series((candle(t0 + timedelta(hours=1)), candle(t0)), "1h")
    assert report.valid is False
    assert "NON_DETERMINISTIC_ORDER" in report.reason_codes


def test_duplicate_identity_is_invalid():
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    report = validate_candle_series((candle(t0), candle(t0)), "1h")
    assert report.valid is False
    assert "DUPLICATE_CANDLE" in report.reason_codes


def test_gap_is_invalid():
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    report = validate_candle_series((candle(t0), candle(t0 + timedelta(hours=2))), "1h")
    assert report.valid is False
    assert "CANDLE_GAP" in report.reason_codes


def test_overlap_is_invalid():
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    first = candle(t0)
    second = Candle(
        symbol="BTCUSDT", timeframe="1h", open_time=t0 + timedelta(minutes=30),
        close_time=t0 + timedelta(hours=1, minutes=30), open=100.0, high=110.0,
        low=90.0, close=105.0, volume=1.0,
    )
    report = validate_candle_series((first, second), "1h")
    assert report.valid is False
    assert "OVERLAPPING_CANDLES" in report.reason_codes


def test_exact_contiguous_series_is_valid():
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    report = validate_candle_series(tuple(candle(t0 + timedelta(hours=i)) for i in range(3)), "1h")
    assert report == validate_candle_series(tuple(candle(t0 + timedelta(hours=i)) for i in range(3)), "1h")
    assert report.valid is True
    assert report.reason_codes == ()


def test_invalid_duration_is_rejected():
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    bad = Candle(
        symbol="BTCUSDT", timeframe="1h", open_time=t0,
        close_time=t0 + timedelta(minutes=59), open=100.0, high=110.0,
        low=90.0, close=105.0, volume=1.0,
    )
    report = validate_candle_series((bad,), "1h")
    assert report.valid is False
    assert "INVALID_CANDLE_DURATION" in report.reason_codes


def test_invalid_timeframe_is_fail_closed():
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    report = validate_candle_series((candle(t0),), "1H")
    assert report.valid is False
    assert report.reason_codes == ("INVALID_TIMEFRAME",)
