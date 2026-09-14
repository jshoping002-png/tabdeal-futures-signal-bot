from datetime import datetime, timezone
from decimal import Decimal

import pytest

from tabdeal_signal.data_sources.market import Candle


def make_candle(**overrides):
    values = {
        "instrument": "BTCUSDT",
        "interval": "1m",
        "opened_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "closed_at": datetime(2026, 1, 1, 0, 1, tzinfo=timezone.utc),
        "open": Decimal("100"),
        "high": Decimal("110"),
        "low": Decimal("90"),
        "close": Decimal("105"),
        "volume": Decimal("2"),
    }
    values.update(overrides)
    return Candle(**values)


def test_candle_accepts_valid_ohlcv():
    candle = make_candle()
    assert candle.instrument == "BTCUSDT"
    assert candle.high == Decimal("110")


@pytest.mark.parametrize("field", ["opened_at", "closed_at"])
def test_candle_requires_timezone_aware_timestamps(field):
    with pytest.raises(ValueError, match="timezone-aware"):
        make_candle(**{field: datetime(2026, 1, 1)})


def test_candle_rejects_invalid_price_range():
    with pytest.raises(ValueError, match="high"):
        make_candle(high=Decimal("101"), close=Decimal("105"))


def test_candle_rejects_negative_volume():
    with pytest.raises(ValueError, match="volume"):
        make_candle(volume=Decimal("-1"))


def test_candle_is_immutable():
    candle = make_candle()
    with pytest.raises((AttributeError, TypeError)):
        candle.close = Decimal("99")
