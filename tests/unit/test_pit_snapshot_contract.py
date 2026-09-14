from datetime import datetime, timedelta, timezone

import pytest

from tabdeal_signal.data.contracts import MarketSnapshot, SnapshotRequest, validate_snapshot_request
from tabdeal_signal.domain.contracts import Candle

UTC = timezone.utc


def make_candle(close_time: datetime, *, symbol: str = "BTCUSDT", timeframe: str = "1h") -> Candle:
    start = close_time - timedelta(hours=1)
    return Candle(symbol, timeframe, start, close_time, 100, 110, 90, 105, 1)


def test_snapshot_rejects_candle_closing_exactly_at_reference_time() -> None:
    reference = datetime(2026, 1, 1, 1, tzinfo=UTC)
    with pytest.raises(ValueError, match="unavailable"):
        MarketSnapshot("snap-1", "source-a", reference, (make_candle(reference),))


def test_snapshot_rejects_future_candle() -> None:
    reference = datetime(2026, 1, 1, 1, tzinfo=UTC)
    future = make_candle(reference + timedelta(seconds=1))
    with pytest.raises(ValueError, match="unavailable"):
        MarketSnapshot("snap-1", "source-a", reference, (future,))


def test_snapshot_requires_utc_reference_time() -> None:
    naive = datetime(2026, 1, 1, 1)
    with pytest.raises(ValueError, match="reference_time must be UTC"):
        SnapshotRequest(("BTCUSDT",), ("1h",), naive)


def test_snapshot_rejects_duplicate_candle_identity() -> None:
    reference = datetime(2026, 1, 1, 2, tzinfo=UTC)
    candle = make_candle(reference - timedelta(seconds=1))
    with pytest.raises(ValueError, match="duplicate candles"):
        MarketSnapshot("snap-1", "source-a", reference, (candle, candle))


def test_snapshot_requires_deterministic_candle_order() -> None:
    reference = datetime(2026, 1, 1, 4, tzinfo=UTC)
    early = make_candle(reference - timedelta(hours=2))
    late = make_candle(reference - timedelta(hours=1))
    with pytest.raises(ValueError, match="deterministic order"):
        MarketSnapshot("snap-1", "source-a", reference, (late, early))


def test_snapshot_is_immutable() -> None:
    reference = datetime(2026, 1, 1, 2, tzinfo=UTC)
    snapshot = MarketSnapshot("snap-1", "source-a", reference, (make_candle(reference - timedelta(seconds=1)),))
    with pytest.raises((AttributeError, TypeError)):
        snapshot.snapshot_id = "changed"  # type: ignore[misc]


def test_request_and_snapshot_reference_times_must_match() -> None:
    reference = datetime(2026, 1, 1, 2, tzinfo=UTC)
    other_reference = reference + timedelta(minutes=1)
    snapshot = MarketSnapshot(
        "snap-1",
        "source-a",
        other_reference,
        (make_candle(other_reference - timedelta(seconds=1)),),
    )
    reasons = validate_snapshot_request(SnapshotRequest(("BTCUSDT",), ("1h",), reference), snapshot)
    assert reasons == ("REFERENCE_TIME_MISMATCH",)


def test_identical_snapshot_inputs_have_identical_contents() -> None:
    reference = datetime(2026, 1, 1, 2, tzinfo=UTC)
    candle = make_candle(reference - timedelta(seconds=1))
    first = MarketSnapshot("snap-1", "source-a", reference, (candle,))
    second = MarketSnapshot("snap-1", "source-a", reference, (candle,))
    assert first == second
    assert first.candles == second.candles
