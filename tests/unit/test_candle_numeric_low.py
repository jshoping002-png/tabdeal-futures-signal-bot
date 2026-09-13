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


def test_candle_requires_numeric_volume():
    with pytest.raises(ValueError, match="volume must be numeric"):
        Candle(
            symbol="BTCUSDT",
            timeframe="1h",
            open_time=datetime(2026, 1, 1, tzinfo=UTC),
            close_time=datetime(2026, 1, 1, 1, tzinfo=UTC),
            open=100.0,
            high=110.0,
            low=90.0,
            close=105.0,
            volume="1",  # type: ignore[arg-type]
        )


def test_candle_requires_datetime_open_time():
    with pytest.raises(ValueError, match="open_time must be a datetime"):
        Candle(
            symbol="BTCUSDT",
            timeframe="1h",
            open_time="2026-01-01T00:00:00Z",  # type: ignore[arg-type]
            close_time=datetime(2026, 1, 1, 1, tzinfo=UTC),
            open=100.0,
            high=110.0,
            low=90.0,
            close=105.0,
            volume=1.0,
        )


def test_candle_requires_datetime_close_time():
    with pytest.raises(ValueError, match="close_time must be a datetime"):
        Candle(
            symbol="BTCUSDT",
            timeframe="1h",
            open_time=datetime(2026, 1, 1, tzinfo=UTC),
            close_time="2026-01-01T01:00:00Z",  # type: ignore[arg-type]
            open=100.0,
            high=110.0,
            low=90.0,
            close=105.0,
            volume=1.0,
        )


def test_candle_availability_requires_datetime_reference_time():
    candle = Candle(
        symbol="BTCUSDT",
        timeframe="1h",
        open_time=datetime(2026, 1, 1, tzinfo=UTC),
        close_time=datetime(2026, 1, 1, 1, tzinfo=UTC),
        open=100.0,
        high=110.0,
        low=90.0,
        close=105.0,
        volume=1.0,
    )

    with pytest.raises(ValueError, match="reference_time must be a datetime"):
        candle.is_available_at("2026-01-01T02:00:00Z")  # type: ignore[arg-type]
