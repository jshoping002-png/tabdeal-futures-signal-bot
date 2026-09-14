from tabdeal_signal.data_sources import (
    DataProvenance,
    DataQualityStatus,
    DataSnapshotMetadata,
    NormalizedSnapshot,
    ReadOnlyDataSource,
    SourceKind,
    StaticDataSource,
)
from tabdeal_signal.data_sources import __all__ as data_source_exports
from tabdeal_signal.data_sources.contracts import (
    DataProvenance as module_provenance,
    DataQualityStatus as module_quality,
    DataSnapshotMetadata as module_metadata,
    NormalizedSnapshot as module_snapshot,
    ReadOnlyDataSource as module_source,
    SourceKind as module_kind,
)
from tabdeal_signal.data_sources.static import StaticDataSource as module_static


def test_data_source_package_exports_match_contract_symbols() -> None:
    assert DataProvenance is module_provenance
    assert DataQualityStatus is module_quality
    assert DataSnapshotMetadata is module_metadata
    assert NormalizedSnapshot is module_snapshot
    assert ReadOnlyDataSource is module_source
    assert SourceKind is module_kind
    assert StaticDataSource is module_static


def test_data_source_package_exports_are_explicit_and_stable() -> None:
    assert data_source_exports == [
        "DataProvenance",
        "DataQualityStatus",
        "DataSnapshotMetadata",
        "NormalizedSnapshot",
        "ReadOnlyDataSource",
        "SourceKind",
        "StaticDataSource",
    ]
