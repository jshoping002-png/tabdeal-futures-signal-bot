"""Immutable, read-only contracts for normalized data snapshots.

This module deliberately contains no trading or order-execution capability.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Mapping, Protocol, TypeAlias


class DataQualityStatus(StrEnum):
    VALID = "VALID"
    STALE = "STALE"
    INCOMPLETE = "INCOMPLETE"
    GAPPED = "GAPPED"
    CONFLICTING = "CONFLICTING"
    INVALID = "INVALID"
    UNAVAILABLE = "UNAVAILABLE"


class SourceKind(StrEnum):
    EXCHANGE = "exchange"
    AGGREGATOR = "aggregator"
    MACRO = "macro"
    NEWS = "news"
    MARKET_INDEX = "market_index"


Payload: TypeAlias = Mapping[str, object]


def _require_aware(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class DataProvenance:
    source: str
    reference: str
    schema_version: str

    def __post_init__(self) -> None:
        for name, value in (
            ("source", self.source),
            ("reference", self.reference),
            ("schema_version", self.schema_version),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")


@dataclass(frozen=True, slots=True)
class DataSnapshotMetadata:
    source_kind: SourceKind
    instrument_or_topic: str
    received_at: datetime
    observed_at: datetime | None = None
    published_at: datetime | None = None
    effective_at: datetime | None = None
    available_at: datetime | None = None
    quality: DataQualityStatus = DataQualityStatus.VALID
    provenance: DataProvenance | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.source_kind, SourceKind):
            raise ValueError("source_kind must be a SourceKind")
        if not isinstance(self.quality, DataQualityStatus):
            raise ValueError("quality must be a DataQualityStatus")
        if self.provenance is not None and not isinstance(self.provenance, DataProvenance):
            raise ValueError("provenance must be DataProvenance")
        if not isinstance(self.instrument_or_topic, str) or not self.instrument_or_topic.strip():
            raise ValueError("instrument_or_topic must be a non-empty string")
        for name in (
            "received_at",
            "observed_at",
            "published_at",
            "effective_at",
            "available_at",
        ):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _require_aware(value, name))

        if self.available_at is not None and self.available_at > self.received_at:
            raise ValueError("available_at cannot be later than received_at")


@dataclass(frozen=True, slots=True)
class NormalizedSnapshot:
    metadata: DataSnapshotMetadata
    values: Payload

    def __post_init__(self) -> None:
        if not isinstance(self.metadata, DataSnapshotMetadata):
            raise ValueError("metadata must be DataSnapshotMetadata")
        if not isinstance(self.values, Mapping):
            raise ValueError("values must be a mapping")
        if any(not isinstance(key, str) for key in self.values):
            raise ValueError("values keys must be strings")


class ReadOnlyDataSource(Protocol):
    """Provider boundary for data retrieval only."""

    def fetch_snapshot(self, *, as_of: datetime | None = None) -> NormalizedSnapshot:
        """Return a normalized snapshot; must not mutate or execute trades."""
        ...


__all__ = [
    "DataProvenance",
    "DataQualityStatus",
    "DataSnapshotMetadata",
    "NormalizedSnapshot",
    "ReadOnlyDataSource",
    "SourceKind",
]
