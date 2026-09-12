from datetime import datetime, timedelta, timezone

import pytest

from tabdeal_signal.data.contracts import MarketSnapshot, SnapshotRequest
from tabdeal_signal.domain.contracts import Candle

UTC = timezone.utc


def candle(minutes: int, symbol: str = "BTCUSDT", timeframe: str = "1h") -> Candle:
    start = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(hours=minutes)
    return Candle(symbol, timeframe, start, start + timedelta(hours=1), 100, 110, 90, 105, 1)


def test_snapshot_rejects_unavailable_candle() -> None:
    c = candle(0)
    with pytest.raises(ValueError, match="unavailable"):
        MarketSnapshot("snap-1", "source-a", c.close_time - timedelta(microseconds=1), (c,))


def test_snapshot_rejects_duplicate_candles() -> None:
    c = candle(0)
    with pytest.raises(ValueError, match="duplicate"):
        MarketSnapshot("snap-1", "source-a", c.close_time, (c, c))


def test_snapshot_requires_deterministic_order() -> None:
    first = candle(0)
    second = candle(1)
    with pytest.raises(ValueError, match="deterministic order"):
        MarketSnapshot("snap-1", "source-a", second.close_time, (second, first))


def test_snapshot_is_immutable_and_filters_without_mutation() -> None:
    first = candle(0)
    second = candle(1)
    snapshot = MarketSnapshot("snap-1", "source-a", second.close_time + timedelta(microseconds=1), (first, second))
    assert snapshot.candles_for("BTCUSDT", "1h") == (first, second)
    with pytest.raises(AttributeError):
        snapshot.snapshot_id = "changed"  # type: ignore[misc]


def test_snapshot_rejects_mutable_candle_collection() -> None:
    c = candle(0)
    with pytest.raises(ValueError, match="candles must be a tuple"):
        MarketSnapshot("snap-1", "source-a", c.close_time + timedelta(microseconds=1), [c])  # type: ignore[arg-type]


def test_snapshot_rejects_non_candle_members() -> None:
    c = candle(0)
    with pytest.raises(ValueError, match="Candle instances"):
        MarketSnapshot("snap-1", "source-a", c.close_time + timedelta(microseconds=1), (c, object()))  # type: ignore[arg-type]


def test_snapshot_rejects_non_datetime_reference_time() -> None:
    c = candle(0)
    with pytest.raises(ValueError, match="datetime"):
        MarketSnapshot("snap-1", "source-a", "2026-01-01T01:00:01Z", (c,))  # type: ignore[arg-type]


def test_snapshot_rejects_non_string_snapshot_id() -> None:
    c = candle(0)
    with pytest.raises(ValueError, match="snapshot_id must be a string"):
        MarketSnapshot(123, "source-a", c.close_time + timedelta(microseconds=1), (c,))  # type: ignore[arg-type]


def test_snapshot_rejects_non_string_source_id() -> None:
    c = candle(0)
    with pytest.raises(ValueError, match="source_id must be a string"):
        MarketSnapshot("snap-1", 123, c.close_time + timedelta(microseconds=1), (c,))  # type: ignore[arg-type]


def test_request_rejects_duplicate_symbols_and_timeframes() -> None:
    ref = datetime(2026, 1, 1, tzinfo=UTC)
    with pytest.raises(ValueError, match="symbols"):
        SnapshotRequest(("BTCUSDT", "BTCUSDT"), ("1h",), ref)
    with pytest.raises(ValueError, match="timeframes"):
        SnapshotRequest(("BTCUSDT",), ("1h", "1h"), ref)


def test_request_rejects_mutable_collections() -> None:
    ref = datetime(2026, 1, 1, tzinfo=UTC)
    with pytest.raises(ValueError, match="tuples"):
        SnapshotRequest(["BTCUSDT"], ("1h",), ref)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="tuples"):
        SnapshotRequest(("BTCUSDT",), ["1h"], ref)  # type: ignore[arg-type]


def test_request_rejects_non_string_symbol_members() -> None:
    ref = datetime(2026, 1, 1, tzinfo=UTC)
    with pytest.raises(ValueError, match="only strings"):
        SnapshotRequest((123,), ("1h",), ref)  # type: ignore[arg-type]


def test_request_rejects_non_string_timeframe_members() -> None:
    ref = datetime(2026, 1, 1, tzinfo=UTC)
    with pytest.raises(ValueError, match="only strings"):
        SnapshotRequest(("BTCUSDT",), (60,), ref)  # type: ignore[arg-type]
