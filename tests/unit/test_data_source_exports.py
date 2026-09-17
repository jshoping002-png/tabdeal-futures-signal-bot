from tabdeal_signal.data_sources import (
    BybitKlineDataSource,
    BybitOrderbookDataSource,
    DataProvenance,
    DataQualityStatus,
    DataSnapshotMetadata,
    JsonTransport,
    NormalizedSnapshot,
    ReadOnlyDataSource,
    SourceKind,
    SourceRegistration,
    SourceStatus,
    StaticDataSource,
    UrllibJsonTransport,
)
from tabdeal_signal.data_sources import __all__ as data_source_exports
from tabdeal_signal.data_sources.bybit import (
    BybitOrderbookDataSource as module_bybit,
    JsonTransport as module_transport,
    UrllibJsonTransport as module_urllib,
)
from tabdeal_signal.data_sources.bybit_kline import BybitKlineDataSource as module_kline
from tabdeal_signal.data_sources.contracts import (
    DataProvenance as module_provenance,
    DataQualityStatus as module_quality,
    DataSnapshotMetadata as module_metadata,
    NormalizedSnapshot as module_snapshot,
    ReadOnlyDataSource as module_source,
    SourceKind as module_kind,
)
from tabdeal_signal.data_sources.registry import (
    SourceRegistration as module_registration,
    SourceStatus as module_status,
)
from tabdeal_signal.data_sources.static import StaticDataSource as module_static


def test_data_source_package_exports_match_contract_symbols() -> None:
    assert DataProvenance is module_provenance
    assert DataQualityStatus is module_quality
    assert DataSnapshotMetadata is module_metadata
    assert NormalizedSnapshot is module_snapshot
    assert ReadOnlyDataSource is module_source
    assert SourceKind is module_kind
    assert SourceRegistration is module_registration
    assert SourceStatus is module_status
    assert StaticDataSource is module_static
    assert BybitOrderbookDataSource is module_bybit
    assert BybitKlineDataSource is module_kline
    assert JsonTransport is module_transport
    assert UrllibJsonTransport is module_urllib


def test_data_source_package_exports_are_explicit_and_stable() -> None:
    assert data_source_exports == [
        "DataProvenance",
        "DataQualityStatus",
        "DataSnapshotMetadata",
        "NormalizedSnapshot",
        "ReadOnlyDataSource",
        "SourceKind",
        "SourceRegistration",
        "SourceStatus",
        "StaticDataSource",
        "BybitOrderbookDataSource",
        "BybitKlineDataSource",
        "JsonTransport",
        "UrllibJsonTransport",
    ]
