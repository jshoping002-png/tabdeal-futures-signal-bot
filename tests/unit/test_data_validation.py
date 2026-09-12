from datetime import datetime, timedelta, timezone
from math import inf, nan

import pytest

from tabdeal_signal.data.contracts import MarketSnapshot, SnapshotRequest
from tabdeal_signal.data.validation import validate_snapshot
from tabdeal_signal.domain.contracts import Candle

UTC = timezone.utc


def candle(hour: int, close: float = 105.0) -> Candle:
    start = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(hours=hour)
    return Candle("BTCUSDT", "1h", start, start + timedelta(hours=1), 100, 110, 90, close, 1)


def request(reference_time: datetime) -> SnapshotRequest:
    return SnapshotRequest(("BTCUSDT",), ("1h",), reference_time)


def snapshot(reference_time: datetime, candle_value: Candle) -> MarketSnapshot:
    return MarketSnapshot("snap-1", "source-a", reference_time, (candle_value,))


def test_valid_snapshot_passes_validation() -> None:
    ref = candle(1).close_time
    report = validate_snapshot(request(ref), snapshot(ref, candle(0)))
    assert report.valid is True
    assert report.issues == ()


def test_missing_requested_pair_blocks() -> None:
    ref = candle(1).close_time
    req = SnapshotRequest(("BTCUSDT", "ETHUSDT"), ("1h",), ref)
    report = validate_snapshot(req, snapshot(ref, candle(0)))
    assert report.valid is False
    assert any(issue.code == "MISSING_DATA" for issue in report.issues)


def test_unrequested_pair_blocks() -> None:
    ref = candle(1).close_time
    req = request(ref)
    extra = Candle("ETHUSDT", "1h", candle(0).open_time, candle(0).close_time, 100, 110, 90, 105, 1)
    snap = MarketSnapshot("snap-1", "source-a", ref, (candle(0), extra))
    report = validate_snapshot(req, snap)
    assert report.valid is False
    assert any(issue.code == "UNREQUESTED_DATA" for issue in report.issues)


def test_non_finite_value_is_rejected_at_candle_boundary() -> None:
    with pytest.raises(ValueError, match="finite"):
        Candle("BTCUSDT", "1h", candle(0).open_time, candle(0).close_time, 100, 110, 90, nan, 1)


def test_non_positive_price_blocks() -> None:
    ref = candle(1).close_time
    bad = Candle("BTCUSDT", "1h", candle(0).open_time, candle(0).close_time, 100, 110, 0, 105, 1)
    report = validate_snapshot(request(ref), snapshot(ref, bad))
    assert report.valid is False
    assert any(issue.code == "NON_POSITIVE_PRICE" for issue in report.issues)


def test_future_candle_is_rejected_by_snapshot_before_validation() -> None:
    ref = candle(0).close_time
    future = candle(1)
    try:
        MarketSnapshot("snap-1", "source-a", ref, (future,))
    except ValueError as exc:
        assert "unavailable" in str(exc)
    else:
        raise AssertionError("future candle must not enter a MarketSnapshot")


def test_validation_report_is_immutable() -> None:
    ref = candle(1).close_time
    report = validate_snapshot(request(ref), snapshot(ref, candle(0)))
    try:
        report.valid = False  # type: ignore[misc]
    except AttributeError:
        pass
    else:
        raise AssertionError("validation report must be immutable")


def test_infinity_is_rejected_at_candle_boundary() -> None:
    with pytest.raises(ValueError, match="finite"):
        Candle("BTCUSDT", "1h", candle(0).open_time, candle(0).close_time, 100, inf, 90, 105, 1)
