from datetime import datetime, timezone
from types import MappingProxyType

from tabdeal_signal.data_sources.contracts import (
    DataSnapshotMetadata,
    DataQualityStatus,
    NormalizedSnapshot,
    SourceKind,
)
from tabdeal_signal.data_sources.static import StaticDataSource


def _snapshot() -> NormalizedSnapshot:
    metadata = DataSnapshotMetadata(
        source_kind=SourceKind.EXCHANGE,
        instrument_or_topic="BTCUSDT",
        received_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        quality=DataQualityStatus.VALID,
    )
    return NormalizedSnapshot(
        metadata=metadata,
        values={"close": 100.0, "volume": 12.5},
    )


def test_static_data_source_returns_deterministic_snapshot() -> None:
    source = StaticDataSource(_snapshot())

    first = source.fetch_snapshot(as_of=datetime(2026, 1, 2, tzinfo=timezone.utc))
    second = source.fetch_snapshot()

    assert first == second
    assert first.values["close"] == 100.0
    assert first.metadata.instrument_or_topic == "BTCUSDT"


def test_static_data_source_copies_fixture_values() -> None:
    original = _snapshot()
    source = StaticDataSource(original)

    assert source.fetch_snapshot().values == {"close": 100.0, "volume": 12.5}
    assert isinstance(source.fetch_snapshot().values, MappingProxyType)
