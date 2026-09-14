"""Deterministic read-only data source backed by an immutable fixture."""

from __future__ import annotations

from datetime import datetime
from types import MappingProxyType
from typing import Mapping

from .contracts import DataSnapshotMetadata, NormalizedSnapshot, ReadOnlyDataSource


class StaticDataSource(ReadOnlyDataSource):
    """Return the same normalized snapshot for every read.

    This adapter is intended for deterministic fixtures and replay tests. It has
    no network, trading, or order-execution capability.
    """

    def __init__(self, snapshot: NormalizedSnapshot) -> None:
        if not isinstance(snapshot, NormalizedSnapshot):
            raise ValueError("snapshot must be a NormalizedSnapshot")
        self._snapshot = NormalizedSnapshot(
            metadata=snapshot.metadata,
            values=MappingProxyType(dict(snapshot.values)),
        )

    def fetch_snapshot(self, *, as_of: datetime | None = None) -> NormalizedSnapshot:
        """Return the fixture; ``as_of`` is accepted for protocol compatibility."""
        del as_of
        return self._snapshot


__all__ = ["StaticDataSource"]
