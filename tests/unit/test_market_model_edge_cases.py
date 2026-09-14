from decimal import Decimal

import pytest

from tabdeal_signal.data_sources.market import Candle
from tests.unit.test_market_models import make_candle


@pytest.mark.parametrize("field", ["open", "low", "close"])
def test_candle_rejects_negative_prices(field):
    with pytest.raises(ValueError, match="prices must be non-negative"):
        make_candle(**{field: Decimal("-0.01")})


def test_candle_rejects_negative_high():
    with pytest.raises(ValueError, match="high"):
        make_candle(high=Decimal("-0.01"))


def test_candle_rejects_non_positive_interval():
    with pytest.raises(ValueError, match="opened_at must be earlier"):
        make_candle(closed_at=make_candle().opened_at)


def test_candle_rejects_blank_instrument_and_interval():
    with pytest.raises(ValueError, match="instrument"):
        make_candle(instrument="   ")
    with pytest.raises(ValueError, match="interval"):
        make_candle(interval="")
