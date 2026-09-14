from datetime import datetime, timezone

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
