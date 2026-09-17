"""Read-only data source contracts and deterministic fixtures."""

from .contracts import (
    DataProvenance,
    DataQualityStatus,
    DataSnapshotMetadata,
    NormalizedSnapshot,
    ReadOnlyDataSource,
    SourceKind,
)
from .registry import SourceRegistration, SourceStatus
from .static import StaticDataSource
from .bybit import BybitOrderbookDataSource, JsonTransport, UrllibJsonTransport

__all__ = [
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
    "JsonTransport",
    "UrllibJsonTransport",
]
