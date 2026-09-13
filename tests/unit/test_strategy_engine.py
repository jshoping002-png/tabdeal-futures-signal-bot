from datetime import datetime, timedelta, timezone

from tabdeal_signal.domain.contracts import Candle
from tabdeal_signal.strategy.engine import _confirmed_swings

UTC = timezone.utc


def make_candle(i, high=10.0, low=1.0):
    start = datetime(2026, 1, 1, tzinfo=UTC) + i * timedelta(minutes=15)
    return Candle("BTCUSDT", "15m", start, start + timedelta(minutes=15), low, high, low, (high + low) / 2, 1.0)


def test_strict_swing_high_is_confirmed_by_two_following_candles():
    candles = tuple(make_candle(i, high=20.0 if i == 2 else 10.0) for i in range(5))
    swings = _confirmed_swings(candles, high=True)
    assert len(swings) == 1
    assert swings[0].index == 2
    assert swings[0].price == 20.0
    assert swings[0].confirmed_at == candles[4].close_time


def test_equal_neighbor_is_not_a_swing():
    candles = tuple(make_candle(i, high=20.0 if i in (2, 3) else 10.0) for i in range(5))
    assert _confirmed_swings(candles, high=True) == ()


def test_strict_swing_low_is_confirmed():
    candles = tuple(make_candle(i, low=0.0 if i == 2 else 1.0) for i in range(5))
    swings = _confirmed_swings(candles, high=False)
    assert len(swings) == 1
    assert swings[0].index == 2
    assert swings[0].price == 0.0
