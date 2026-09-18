from datetime import datetime, timezone

import pytest

from tabdeal_signal.data_sources.contracts import (
    DataProvenance,
    DataQualityStatus,
    DataSnapshotMetadata,
    NormalizedSnapshot,
    SourceKind,
)
from tabdeal_signal.data_sources.replay import ReplayFixtureDataSource, SnapshotFixtureCodec

UTC = timezone.utc


def snapshot(*, available_at: datetime, value: int, quality=DataQualityStatus.VALID) -> NormalizedSnapshot:
    return NormalizedSnapshot(
        metadata=DataSnapshotMetadata(
            source_kind=SourceKind.MACRO,
            instrument_or_topic="fixture",
            received_at=available_at,
            observed_at=available_at,
            published_at=available_at,
            effective_at=available_at,
            available_at=available_at,
            quality=quality,
            provenance=DataProvenance("fixture-source", "fixture://001-2040", "1"),
        ),
        values={"value": value},
    )


def test_fixture_codec_round_trip_is_deterministic():
    source = snapshot(available_at=datetime(2026, 1, 1, 0, 0, tzinfo=UTC), value=7)
    encoded_a = SnapshotFixtureCodec.encode(source)
    encoded_b = SnapshotFixtureCodec.encode(source)
    assert encoded_a == encoded_b
    restored = SnapshotFixtureCodec.decode(encoded_a)
    assert restored == source


def test_replay_uses_latest_snapshot_available_at_or_before_as_of():
    first = snapshot(available_at=datetime(2026, 1, 1, tzinfo=UTC), value=1)
    second = snapshot(available_at=datetime(2026, 1, 2, tzinfo=UTC), value=2)
    replay = ReplayFixtureDataSource([second, first])
    result = replay.fetch_snapshot(as_of=datetime(2026, 1, 1, 12, tzinfo=UTC))
    assert result.values["value"] == 1


def test_replay_blocks_when_no_snapshot_precedes_as_of():
    first = snapshot(available_at=datetime(2026, 1, 1, tzinfo=UTC), value=1)
    replay = ReplayFixtureDataSource([first])
    result = replay.fetch_snapshot(as_of=datetime(2025, 12, 31, 23, 59, 59, tzinfo=UTC))
    assert result.metadata.quality is DataQualityStatus.UNAVAILABLE
    assert result.values["error_class"] == "pit_unavailable"


def test_replay_requires_available_at_and_strict_time_order():
    missing = NormalizedSnapshot(
        metadata=DataSnapshotMetadata(
            source_kind=SourceKind.MACRO,
            instrument_or_topic="fixture",
            received_at=datetime(2026, 1, 1, tzinfo=UTC),
        ),
        values={"value": 1},
    )
    with pytest.raises(ValueError, match="require available_at"):
        ReplayFixtureDataSource([missing])

    same = snapshot(available_at=datetime(2026, 1, 1, tzinfo=UTC), value=1)
    with pytest.raises(ValueError, match="strictly increasing"):
        ReplayFixtureDataSource([same, same])


def test_codec_rejects_unsupported_fixture_version():
    with pytest.raises(ValueError, match="unsupported fixture format version"):
        SnapshotFixtureCodec.decode(b'{"format_version":"999"}')


@pytest.mark.parametrize(
    "field,value",
    [
        ("source", None),
        ("reference", None),
        ("schema_version", None),
        ("source", 123),
        ("reference", 123),
        ("schema_version", 123),
        ("source", ""),
        ("reference", " "),
        ("schema_version", ""),
    ],
)
def test_codec_rejects_invalid_provenance_fields(field, value):
    raw = SnapshotFixtureCodec.encode(snapshot(available_at=datetime(2026, 1, 1, tzinfo=UTC), value=1))
    import json

    payload = json.loads(raw)
    payload["metadata"]["provenance"][field] = value
    tampered = json.dumps(payload).encode("utf-8")

    with pytest.raises(ValueError, match="invalid fixture provenance"):
        SnapshotFixtureCodec.decode(tampered)
