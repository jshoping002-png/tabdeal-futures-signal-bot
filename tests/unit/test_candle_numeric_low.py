from datetime import datetime, timezone

import pytest

from tabdeal_signal.domain.contracts import Candle

UTC = timezone.utc


def test_candle_requires_numeric_low():
    with pytest.raises(ValueError, match="low must be numeric"):
        Candle(
            symbol="BTCUSDT",
            timeframe="1h",
            open_time=datetime(2026, 1, 1, tzinfo=UTC),
            close_time=datetime(2026, 1, 1, 1, tzinfo=UTC),
            open=100.0,
            high=110.0,
            low="90",  # type: ignore[arg-type]
            close=105.0,
            volume=1.0,
        )


def test_candle_requires_numeric_close():
    with pytest.raises(ValueError, match="close must be numeric"):
        Candle(
            symbol="BTCUSDT",
            timeframe="1h",
            open_time=datetime(2026, 1, 1, tzinfo=UTC),
            close_time=datetime(2026, 1, 1, 1, tzinfo=UTC),
            open=100.0,
            high=110.0,
            low=90.0,
            close="105",  # type: ignore[arg-type]
            volume=1.0,
        )
