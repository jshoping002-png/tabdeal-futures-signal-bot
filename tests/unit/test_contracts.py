from datetime import datetime, timedelta, timezone

import pytest

from tabdeal_signal.domain.contracts import Candle, DecisionContext, DecisionStatus, Direction, SideDecision

UTC = timezone.utc


def candle(**overrides):
    values = dict(symbol="BTCUSDT", timeframe="1h", open_time=datetime(2026, 1, 1, tzinfo=UTC), close_time=datetime(2026, 1, 1, 1, tzinfo=UTC), open=100.0, high=110.0, low=90.0, close=105.0, volume=1.0)
    values.update(overrides)
    return Candle(**values)


def test_valid_closed_candle_is_accepted():
    assert candle().close > candle().open


def test_candle_is_available_only_before_close_boundary():
    item = candle()
    assert not item.is_available_at(datetime(2026, 1, 1, 0, 59, 59, tzinfo=UTC))
    assert not item.is_available_at(datetime(2026, 1, 1, 1, tzinfo=UTC))
    assert item.is_available_at(datetime(2026, 1, 1, 1, 0, 1, tzinfo=UTC))


def test_candle_availability_rejects_non_utc_reference_time():
    with pytest.raises(ValueError, match="UTC"):
        candle().is_available_at(datetime(2026, 1, 1, 1))


def test_naive_candle_timestamp_is_rejected():
    with pytest.raises(ValueError, match="timezone-aware"):
        candle(open_time=datetime(2026, 1, 1))


def test_non_utc_candle_timestamp_is_rejected():
    plus_one = timezone(timedelta(hours=1))
    with pytest.raises(ValueError, match="UTC"):
        candle(open_time=datetime(2026, 1, 1, tzinfo=plus_one))


def test_non_finite_candle_numeric_value_is_rejected():
    with pytest.raises(ValueError, match="finite"):
        candle(close=float("nan"))
    with pytest.raises(ValueError, match="finite"):
        candle(volume=float("inf"))


def test_invalid_ohlc_is_rejected():
    with pytest.raises(ValueError, match="OHLC"):
        candle(high=99.0)


def test_empty_timeframe_is_rejected():
    with pytest.raises(ValueError, match="timeframe"):
        candle(timeframe=" ")


def test_future_reference_time_is_rejected():
    with pytest.raises(ValueError, match="after"):
        DecisionContext(decision_time=datetime(2026, 1, 1, tzinfo=UTC), reference_time=datetime(2026, 1, 1, 1, tzinfo=UTC), snapshot_id="s1", config_version="v1")


def test_decision_context_rejects_non_datetime_decision_time():
    with pytest.raises(ValueError, match="decision_time must be a datetime"):
        DecisionContext(
            decision_time="2026-01-01T01:00:00Z",  # type: ignore[arg-type]
            reference_time=datetime(2026, 1, 1, 1, tzinfo=UTC),
            snapshot_id="s1",
            config_version="v1",
        )


def test_decision_context_rejects_non_datetime_reference_time():
    with pytest.raises(ValueError, match="reference_time must be a datetime"):
        DecisionContext(
            decision_time=datetime(2026, 1, 1, 1, tzinfo=UTC),
            reference_time="2026-01-01T01:00:00Z",  # type: ignore[arg-type]
            snapshot_id="s1",
            config_version="v1",
        )


def test_direction_is_explicitly_isolated():
    assert Direction.LONG.value != Direction.SHORT.value


def test_side_decision_requires_direction_enum():
    with pytest.raises(ValueError, match="Direction"):
        SideDecision("LONG", DecisionStatus.SIGNAL, "LONG_OK")


def test_side_decision_requires_status_enum():
    with pytest.raises(ValueError, match="DecisionStatus"):
        SideDecision(Direction.LONG, "SIGNAL", "LONG_OK")


def test_decision_context_requires_string_ids():
    with pytest.raises(ValueError, match="strings"):
        DecisionContext(
            decision_time=datetime(2026, 1, 1, 1, tzinfo=UTC),
            reference_time=datetime(2026, 1, 1, 1, tzinfo=UTC),
            snapshot_id=["snap-1"],  # type: ignore[arg-type]
            config_version="v1",
        )
    with pytest.raises(ValueError, match="strings"):
        DecisionContext(
            decision_time=datetime(2026, 1, 1, 1, tzinfo=UTC),
            reference_time=datetime(2026, 1, 1, 1, tzinfo=UTC),
            snapshot_id="snap-1",
            config_version=["v1"],  # type: ignore[arg-type]
        )


def test_signal_decision_requires_string_signal_id():
    from tabdeal_signal.domain.contracts import SignalDecision

    with pytest.raises(ValueError, match="signal_id must be a string"):
        SignalDecision(
            signal_id=123,  # type: ignore[arg-type]
            direction=Direction.LONG,
            created_at=datetime(2026, 1, 1, 1, tzinfo=UTC),
            snapshot_id="s1",
            config_version="v1",
            reason_code="LONG_OK",
        )


def test_signal_decision_rejects_non_datetime_created_at():
    from tabdeal_signal.domain.contracts import SignalDecision

    with pytest.raises(ValueError, match="created_at must be a datetime"):
        SignalDecision(
            signal_id="sig-1",
            direction=Direction.LONG,
            created_at="2026-01-01T01:00:00Z",  # type: ignore[arg-type]
            snapshot_id="s1",
            config_version="v1",
            reason_code="LONG_OK",
        )


def test_signal_decision_requires_string_snapshot_id():
    from tabdeal_signal.domain.contracts import SignalDecision

    with pytest.raises(ValueError, match="snapshot_id must be a string"):
        SignalDecision(
            signal_id="sig-1",
            direction=Direction.LONG,
            created_at=datetime(2026, 1, 1, 1, tzinfo=UTC),
            snapshot_id=123,  # type: ignore[arg-type]
            config_version="v1",
            reason_code="LONG_OK",
        )


def test_signal_decision_requires_string_config_version():
    from tabdeal_signal.domain.contracts import SignalDecision

    with pytest.raises(ValueError, match="config_version must be a string"):
        SignalDecision(
            signal_id="sig-1",
            direction=Direction.LONG,
            created_at=datetime(2026, 1, 1, 1, tzinfo=UTC),
            snapshot_id="s1",
            config_version=123,  # type: ignore[arg-type]
            reason_code="LONG_OK",
        )
