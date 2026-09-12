from datetime import datetime, timedelta, timezone

import pytest

from tabdeal_signal.domain.contracts import Candle, DecisionContext, Direction


UTC = timezone.utc


def candle(**overrides):
    values = dict(
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
    values.update(overrides)
    return Candle(**values)


def test_valid_closed_candle_is_accepted():
    assert candle().close > candle().open


def test_naive_candle_timestamp_is_rejected():
    with pytest.raises(ValueError, match="timezone-aware"):
        candle(open_time=datetime(2026, 1, 1))


def test_non_utc_candle_timestamp_is_rejected():
    plus_one = timezone(timedelta(hours=1))
    with pytest.raises(ValueError, match="UTC"):
        candle(open_time=datetime(2026, 1, 1, tzinfo=plus_one))


def test_invalid_ohlc_is_rejected():
    with pytest.raises(ValueError, match="OHLC"):
        candle(high=99.0)


def test_future_reference_time_is_rejected():
    with pytest.raises(ValueError, match="after"):
        DecisionContext(
            decision_time=datetime(2026, 1, 1, tzinfo=UTC),
            reference_time=datetime(2026, 1, 1, 1, tzinfo=UTC),
            snapshot_id="s1",
            config_version="v1",
        )


def test_direction_is_explicitly_isolated():
    assert Direction.LONG.value != Direction.SHORT.value
