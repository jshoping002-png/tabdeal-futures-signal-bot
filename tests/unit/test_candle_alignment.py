from datetime import datetime, timedelta

import pytest

from tabdeal_signal.data.alignment import AlignmentPolicy, select_closed_candles, validate_alignment
from tabdeal_signal.data.series import TimeframeSpec
from tabdeal_signal.domain.contracts import Candle, UTC


def make_candle(open_time: datetime) -> Candle:
    return Candle(
        symbol="BTCUSDT",
        timeframe="1h",
        open_time=open_time,
        close_time=open_time + timedelta(hours=1),
        open=100.0,
        high=110.0,
        low=90.0,
        close=105.0,
        volume=1.0,
    )


def test_closed_candle_requires_strict_close_boundary():
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    candles = (make_candle(t0), make_candle(t0 + timedelta(hours=1)))
    assert select_closed_candles(candles, t0 + timedelta(hours=2)) == (candles[0],)


def test_future_candle_is_not_selected():
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    candles = (make_candle(t0), make_candle(t0 + timedelta(hours=1)))
    assert select_closed_candles(candles, t0 + timedelta(hours=1)) == ()


def test_non_utc_reference_is_rejected():
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    with pytest.raises(ValueError):
        select_closed_candles((make_candle(t0),), datetime(2026, 1, 1, 2))


def test_alignment_boundary_is_explicit_and_deterministic():
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    policy = AlignmentPolicy(TimeframeSpec.parse("1h"), t0)
    candles = (make_candle(t0), make_candle(t0 + timedelta(hours=1)))
    assert validate_alignment(candles, policy) == ()
    assert validate_alignment(candles, policy) == ()


def test_alignment_rejects_non_aligned_boundary():
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    policy = AlignmentPolicy(TimeframeSpec.parse("1h"), t0)
    shifted = make_candle(t0 + timedelta(minutes=30))
    assert validate_alignment((shifted,), policy) == ("CANDLE_BOUNDARY_MISMATCH",)
