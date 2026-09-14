from datetime import datetime, timedelta, timezone

import pytest

from tabdeal_signal.data.contracts import MarketSnapshot, SnapshotRequest
from tabdeal_signal.data.ingestion import MarketDataIngestionError, ingest
from tabdeal_signal.data.in_memory_source import InMemoryMarketDataSource
from tabdeal_signal.domain.contracts import Candle

UTC = timezone.utc


def candle(hour: int, symbol: str = "BTCUSDT", timeframe: str = "1h") -> Candle:
    start = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(hours=hour)
    return Candle(symbol, timeframe, start, start + timedelta(hours=1), 100, 110, 90, 105, 1)


def test_source_returns_exact_registered_point_in_time_snapshot() -> None:
    reference = candle(2).close_time + timedelta(microseconds=1)
    request = SnapshotRequest(("BTCUSDT",), ("1h",), reference)
    snapshot = MarketSnapshot("snap-1", "fixture-source", reference, (candle(0), candle(1)))
    source = InMemoryMarketDataSource("fixture-source")
    source.register(request, snapshot)

    result = ingest(source, request)

    assert result.snapshot == snapshot
    assert result.validation.valid is True


def test_source_fails_closed_when_requested_snapshot_is_missing() -> None:
    reference = candle(1).close_time
    request = SnapshotRequest(("BTCUSDT",), ("1h",), reference)
    source = InMemoryMarketDataSource("fixture-source")

    with pytest.raises(LookupError, match="unavailable"):
        source.snapshot(request)


def test_source_rejects_different_source_identity() -> None:
    reference = candle(1).close_time
    request = SnapshotRequest(("BTCUSDT",), ("1h",), reference)
    snapshot = MarketSnapshot("snap-1", "other-source", reference, (candle(0),))
    source = InMemoryMarketDataSource("fixture-source")

    with pytest.raises(ValueError, match="source_id"):
        source.register(request, snapshot)


def test_source_rejects_duplicate_request_with_different_snapshot() -> None:
    reference = candle(2).close_time
    request = SnapshotRequest(("BTCUSDT",), ("1h",), reference)
    first = MarketSnapshot("snap-1", "fixture-source", reference, (candle(0), candle(1)))
    second = MarketSnapshot("snap-2", "fixture-source", reference, (candle(0), candle(1)))
    source = InMemoryMarketDataSource("fixture-source")
    source.register(request, first)

    with pytest.raises(ValueError, match="different data"):
        source.register(request, second)


def test_ingestion_rejects_source_identity_mismatch() -> None:
    reference = candle(1).close_time
    request = SnapshotRequest(("BTCUSDT",), ("1h",), reference)

    class WrongIdentitySource:
        source_id = "expected"

        def snapshot(self, _request: SnapshotRequest) -> MarketSnapshot:
            return MarketSnapshot("snap-1", "actual", reference, (candle(0),))

    with pytest.raises(MarketDataIngestionError, match="identity"):
        ingest(WrongIdentitySource(), request)


def test_ingestion_rejects_scope_violation() -> None:
    reference = candle(1).close_time
    request = SnapshotRequest(("BTCUSDT",), ("1h",), reference)
    snapshot = MarketSnapshot("snap-1", "fixture-source", reference, (candle(0, "ETHUSDT"),))
    source = InMemoryMarketDataSource("fixture-source")

    with pytest.raises(ValueError, match="scope"):
        source.register(request, snapshot)


def test_registration_is_idempotent_for_same_request_and_snapshot() -> None:
    reference = candle(1).close_time
    request = SnapshotRequest(("BTCUSDT",), ("1h",), reference)
    snapshot = MarketSnapshot("snap-1", "fixture-source", reference, (candle(0),))
    source = InMemoryMarketDataSource("fixture-source")

    source.register(request, snapshot)
    source.register(request, snapshot)

    assert source.snapshot(request) == snapshot
