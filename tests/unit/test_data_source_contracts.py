from datetime import datetime, timedelta, timezone
from inspect import signature
from types import MappingProxyType

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


def test_metadata_normalizes_all_optional_timestamps_to_utc() -> None:
    offset = timezone(timedelta(hours=5, minutes=30))
    metadata = DataSnapshotMetadata(
        source_kind=SourceKind.NEWS,
        instrument_or_topic="headline",
        received_at=datetime(2026, 1, 1, 5, 30, tzinfo=offset),
        observed_at=datetime(2026, 1, 1, 10, 0, tzinfo=offset),
        published_at=datetime(2026, 1, 1, 9, 0, tzinfo=offset),
        effective_at=datetime(2026, 1, 1, 9, 15, tzinfo=offset),
        available_at=datetime(2026, 1, 1, 5, 30, tzinfo=offset),
    )

    assert metadata.received_at == datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert metadata.observed_at == datetime(2026, 1, 1, 4, 30, tzinfo=timezone.utc)
    assert metadata.published_at == datetime(2026, 1, 1, 3, 30, tzinfo=timezone.utc)
    assert metadata.effective_at == datetime(2026, 1, 1, 3, 45, tzinfo=timezone.utc)
    assert metadata.available_at == datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_naive_timestamp_is_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        DataSnapshotMetadata(
            source_kind=SourceKind.EXCHANGE,
            instrument_or_topic="BTCUSDT",
            received_at=datetime(2026, 1, 1),
        )


def test_invalid_typed_metadata_fields_are_rejected() -> None:
    with pytest.raises(ValueError, match="source_kind"):
        DataSnapshotMetadata("exchange", "BTCUSDT", datetime(2026, 1, 1, tzinfo=timezone.utc))

    with pytest.raises(ValueError, match="quality"):
        DataSnapshotMetadata(
            SourceKind.EXCHANGE,
            "BTCUSDT",
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            quality="VALID",
        )


def test_available_at_cannot_be_after_received_at() -> None:
    with pytest.raises(ValueError, match="available_at"):
        DataSnapshotMetadata(
            source_kind=SourceKind.EXCHANGE,
            instrument_or_topic="BTCUSDT",
            received_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            available_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
        )


def test_snapshot_rejects_invalid_metadata_type() -> None:
    with pytest.raises(ValueError, match="metadata"):
        NormalizedSnapshot(metadata="invalid", values={"close": 100.0})


def test_snapshot_rejects_non_mapping_values() -> None:
    with pytest.raises(ValueError, match="values"):
        NormalizedSnapshot(metadata=_metadata(), values=[("close", 100.0)])


def test_snapshot_rejects_non_string_value_keys() -> None:
    with pytest.raises(ValueError, match="keys must be strings"):
        NormalizedSnapshot(metadata=_metadata(), values={1: 100.0})


def test_snapshot_accepts_mapping_values() -> None:
    snapshot = NormalizedSnapshot(_metadata(), {"close": 100.0, "volume": 12.5})
    assert snapshot.values["close"] == 100.0
    assert snapshot.values["volume"] == 12.5


def test_snapshot_accepts_read_only_mapping_values() -> None:
    values = MappingProxyType({"close": 100.0, "volume": 12.5})
    snapshot = NormalizedSnapshot(_metadata(), values)
    assert snapshot.values is values
    assert snapshot.values["close"] == 100.0


def test_read_only_mapping_rejects_mutation() -> None:
    values = MappingProxyType({"close": 100.0})
    with pytest.raises(TypeError):
        values["close"] = 101.0


def test_provenance_is_immutable() -> None:
    provenance = DataProvenance("test", "fixture://btc", "1")
    with pytest.raises((AttributeError, TypeError)):
        provenance.source = "changed"


def test_metadata_is_immutable() -> None:
    metadata = _metadata()
    with pytest.raises((AttributeError, TypeError)):
        metadata.quality = DataQualityStatus.STALE


def test_snapshot_is_immutable_and_quality_is_explicit() -> None:
    snapshot = NormalizedSnapshot(_metadata(), {"close": 100.0})
    assert snapshot.metadata.quality is DataQualityStatus.VALID
    with pytest.raises((AttributeError, TypeError)):
        snapshot.values = {}


def test_read_only_data_source_signature_is_stable() -> None:
    fetch_snapshot = signature(ReadOnlyDataSource.fetch_snapshot)
    assert list(fetch_snapshot.parameters) == ["self", "as_of"]
    assert fetch_snapshot.parameters["as_of"].kind is fetch_snapshot.parameters["as_of"].KEYWORD_ONLY


def test_read_only_data_source_return_contract_is_explicit() -> None:
    fetch_snapshot = signature(ReadOnlyDataSource.fetch_snapshot)
    assert fetch_snapshot.return_annotation in ("NormalizedSnapshot", NormalizedSnapshot)


def test_read_only_data_source_as_of_is_optional() -> None:
    fetch_snapshot = signature(ReadOnlyDataSource.fetch_snapshot)
    assert fetch_snapshot.parameters["as_of"].default is None


def test_read_only_data_source_as_of_annotation_is_optional_datetime() -> None:
    fetch_snapshot = signature(ReadOnlyDataSource.fetch_snapshot)
    annotation = fetch_snapshot.parameters["as_of"].annotation
    assert annotation in ("datetime | None", datetime | None)


def test_contract_has_only_read_only_fetch_boundary() -> None:
    assert hasattr(ReadOnlyDataSource, "fetch_snapshot")
    assert not any(name in dir(ReadOnlyDataSource) for name in ("place_order", "execute_trade", "cancel_order"))


def test_metadata_defaults_are_explicit_and_safe() -> None:
    metadata = DataSnapshotMetadata(
        source_kind=SourceKind.EXCHANGE,
        instrument_or_topic="BTCUSDT",
        received_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    assert metadata.quality is DataQualityStatus.VALID
    assert metadata.observed_at is None
    assert metadata.published_at is None
    assert metadata.effective_at is None
    assert metadata.available_at is None
    assert metadata.provenance is None
