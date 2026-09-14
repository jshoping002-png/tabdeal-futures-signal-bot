from datetime import datetime, timezone

import pytest

from tabdeal_signal.data_sources.contracts import (
    DataProvenance,
    DataQualityStatus,
    DataSnapshotMetadata,
    NormalizedSnapshot,
    ReadOnlyDataSource,
    SourceKind,
)


def _metadata() -> DataSnapshotMetadata:
    return DataSnapshotMetadata(
        source_kind=SourceKind.EXCHANGE,
        instrument_or_topic="BTCUSDT",
        received_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        available_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        quality=DataQualityStatus.VALID,
        provenance=DataProvenance("test", "fixture://btc", "1"),
    )


def test_metadata_normalizes_aware_timestamps_to_utc() -> None:
    metadata = DataSnapshotMetadata(
        source_kind=SourceKind.MACRO,
        instrument_or_topic="CPI",
        received_at=datetime(2026, 1, 1, 5, tzinfo=timezone.utc),
    )
    assert metadata.received_at.tzinfo == timezone.utc


def test_naive_timestamp_is_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        DataSnapshotMetadata(
            source_kind=SourceKind.EXCHANGE,
            instrument_or_topic="BTCUSDT",
            received_at=datetime(2026, 1, 1),
        )


def test_available_at_cannot_be_after_received_at() -> None:
    with pytest.raises(ValueError, match="available_at"):
        DataSnapshotMetadata(
            source_kind=SourceKind.EXCHANGE,
            instrument_or_topic="BTCUSDT",
            received_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            available_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
        )


def test_snapshot_is_immutable_and_quality_is_explicit() -> None:
    snapshot = NormalizedSnapshot(_metadata(), {"close": 100.0})
    assert snapshot.metadata.quality is DataQualityStatus.VALID
    with pytest.raises((AttributeError, TypeError)):
        snapshot.values = {}


def test_contract_has_only_read_only_fetch_boundary() -> None:
    assert hasattr(ReadOnlyDataSource, "fetch_snapshot")
    assert not any(name in dir(ReadOnlyDataSource) for name in ("place_order", "execute_trade", "cancel_order"))
