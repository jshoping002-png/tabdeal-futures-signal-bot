from datetime import datetime, timedelta, timezone

import pytest

from tabdeal_signal.data_sources.contracts import (
    DataProvenance,
    DataSnapshotMetadata,
    SourceKind,
)


def _received_at() -> datetime:
    return datetime(2026, 1, 1, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    "field_name, value",
    [
        ("source", ""),
        ("source", "  "),
        ("reference", ""),
        ("reference", "  "),
        ("schema_version", ""),
        ("schema_version", "  "),
    ],
)
def test_provenance_rejects_blank_required_fields(field_name: str, value: str) -> None:
    values = {"source": "fixture", "reference": "fixture://btc", "schema_version": "1"}
    values[field_name] = value

    with pytest.raises(ValueError, match=field_name):
        DataProvenance(**values)


def test_metadata_rejects_blank_instrument_or_topic() -> None:
    with pytest.raises(ValueError, match="instrument_or_topic"):
        DataSnapshotMetadata(
            source_kind=SourceKind.EXCHANGE,
            instrument_or_topic="  ",
            received_at=_received_at(),
        )


def test_metadata_accepts_optional_provenance_absence() -> None:
    metadata = DataSnapshotMetadata(
        source_kind=SourceKind.MACRO,
        instrument_or_topic="CPI",
        received_at=_received_at(),
    )

    assert metadata.provenance is None


def test_metadata_normalizes_all_optional_timestamps_to_utc() -> None:
    offset = timezone(timedelta(hours=3))
    metadata = DataSnapshotMetadata(
        source_kind=SourceKind.EXCHANGE,
        instrument_or_topic="BTCUSDT",
        received_at=datetime(2026, 1, 1, 12, tzinfo=offset),
        observed_at=datetime(2026, 1, 1, 13, tzinfo=offset),
        published_at=datetime(2026, 1, 1, 14, tzinfo=offset),
        effective_at=datetime(2026, 1, 1, 15, tzinfo=offset),
        available_at=datetime(2026, 1, 1, 12, tzinfo=offset),
    )

    assert metadata.received_at == datetime(2026, 1, 1, 9, tzinfo=timezone.utc)
    assert metadata.observed_at == datetime(2026, 1, 1, 10, tzinfo=timezone.utc)
    assert metadata.published_at == datetime(2026, 1, 1, 11, tzinfo=timezone.utc)
    assert metadata.effective_at == datetime(2026, 1, 1, 12, tzinfo=timezone.utc)
    assert metadata.available_at == datetime(2026, 1, 1, 9, tzinfo=timezone.utc)


def test_metadata_rejects_non_datetime_timestamp() -> None:
    with pytest.raises(ValueError, match="received_at"):
        DataSnapshotMetadata(
            source_kind=SourceKind.EXCHANGE,
            instrument_or_topic="BTCUSDT",
            received_at="2026-01-01T00:00:00Z",
        )
