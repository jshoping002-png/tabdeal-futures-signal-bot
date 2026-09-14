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


@pytest.mark.parametrize("field", ["open", "high", "low", "close"])
def test_candle_rejects_negative_prices(field):
    with pytest.raises(ValueError, match="prices must be non-negative"):
        make_candle(**{field: Decimal("-0.01")})


def test_candle_rejects_non_positive_interval():
    with pytest.raises(ValueError, match="opened_at must be earlier"):
        make_candle(closed_at=make_candle().opened_at)


def test_candle_rejects_blank_instrument_and_interval():
    with pytest.raises(ValueError, match="instrument"):
        make_candle(instrument="   ")
    with pytest.raises(ValueError, match="interval"):
        make_candle(interval="")
