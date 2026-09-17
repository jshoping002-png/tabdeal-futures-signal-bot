"""Deterministic PIT snapshot fixtures and offline replay source."""
from __future__ import annotations

from bisect import bisect_right
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from json import JSONDecodeError, dumps, loads
from types import MappingProxyType

from .contracts import (
    DataProvenance,
    DataQualityStatus,
    DataSnapshotMetadata,
    NormalizedSnapshot,
    ReadOnlyDataSource,
    SourceKind,
)


FIXTURE_FORMAT_VERSION = "1"


def _utc(value: datetime, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _encode_time(value: datetime | None) -> str | None:
    return None if value is None else _utc(value, "datetime").isoformat()


def _decode_time(value: object, field: str) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO datetime string or null")
    try:
        return _utc(datetime.fromisoformat(value), field)
    except ValueError as exc:
        raise ValueError(f"{field} must be a valid timezone-aware ISO datetime") from exc


class SnapshotFixtureCodec:
    """Serialize/deserialize a single normalized snapshot deterministically."""

    @staticmethod
    def encode(snapshot: NormalizedSnapshot) -> bytes:
        if not isinstance(snapshot, NormalizedSnapshot):
            raise ValueError("snapshot must be a NormalizedSnapshot")
        metadata = snapshot.metadata
        payload = {
            "format_version": FIXTURE_FORMAT_VERSION,
            "metadata": {
                "source_kind": metadata.source_kind.value,
                "instrument_or_topic": metadata.instrument_or_topic,
                "received_at": _encode_time(metadata.received_at),
                "observed_at": _encode_time(metadata.observed_at),
                "published_at": _encode_time(metadata.published_at),
                "effective_at": _encode_time(metadata.effective_at),
                "available_at": _encode_time(metadata.available_at),
                "quality": metadata.quality.value,
                "provenance": None
                if metadata.provenance is None
                else {
                    "source": metadata.provenance.source,
                    "reference": metadata.provenance.reference,
                    "schema_version": metadata.provenance.schema_version,
                },
            },
            "values": dict(snapshot.values),
        }
        try:
            return dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise ValueError("snapshot values must be JSON-serializable for deterministic fixtures") from exc

    @staticmethod
    def decode(raw: bytes) -> NormalizedSnapshot:
        if not isinstance(raw, bytes):
            raise ValueError("raw fixture must be bytes")
        try:
            payload = loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, JSONDecodeError) as exc:
            raise ValueError("fixture must contain valid UTF-8 JSON") from exc
        if not isinstance(payload, Mapping) or payload.get("format_version") != FIXTURE_FORMAT_VERSION:
            raise ValueError("unsupported fixture format version")
        metadata = payload.get("metadata")
        if not isinstance(metadata, Mapping):
            raise ValueError("fixture metadata must be an object")
        try:
            source_kind = SourceKind(metadata["source_kind"])
            quality = DataQualityStatus(metadata["quality"])
            topic = metadata["instrument_or_topic"]
            received_at = _decode_time(metadata["received_at"], "received_at")
            observed_at = _decode_time(metadata.get("observed_at"), "observed_at")
            published_at = _decode_time(metadata.get("published_at"), "published_at")
            effective_at = _decode_time(metadata.get("effective_at"), "effective_at")
            available_at = _decode_time(metadata.get("available_at"), "available_at")
        except (KeyError, ValueError) as exc:
            raise ValueError("invalid fixture metadata") from exc
        if not isinstance(topic, str) or not topic.strip() or received_at is None:
            raise ValueError("fixture topic and received_at are required")
        provenance_data = metadata.get("provenance")
        provenance = None
        if provenance_data is not None:
            if not isinstance(provenance_data, Mapping):
                raise ValueError("fixture provenance must be an object or null")
            try:
                provenance = DataProvenance(
                    str(provenance_data["source"]),
                    str(provenance_data["reference"]),
                    str(provenance_data["schema_version"]),
                )
            except (KeyError, ValueError) as exc:
                raise ValueError("invalid fixture provenance") from exc
        values = payload.get("values")
        if not isinstance(values, Mapping) or any(not isinstance(key, str) for key in values):
            raise ValueError("fixture values must be an object with string keys")
        return NormalizedSnapshot(
            metadata=DataSnapshotMetadata(
                source_kind=source_kind,
                instrument_or_topic=topic,
                received_at=received_at,
                observed_at=observed_at,
                published_at=published_at,
                effective_at=effective_at,
                available_at=available_at,
                quality=quality,
                provenance=provenance,
            ),
            values=MappingProxyType(dict(values)),
        )


class ReplayFixtureDataSource(ReadOnlyDataSource):
    """Offline PIT replay source backed by immutable normalized snapshots."""

    def __init__(self, snapshots: Sequence[NormalizedSnapshot]) -> None:
        if not snapshots:
            raise ValueError("snapshots must not be empty")
        copied = []
        for snapshot in snapshots:
            if not isinstance(snapshot, NormalizedSnapshot):
                raise ValueError("snapshots must contain NormalizedSnapshot instances")
            if snapshot.metadata.available_at is None:
                raise ValueError("replay snapshots require available_at")
            copied.append(snapshot)
        copied.sort(key=lambda item: item.metadata.available_at)
        available_times = [item.metadata.available_at for item in copied]
        assert all(time is not None for time in available_times)
        if any(left >= right for left, right in zip(available_times, available_times[1:])):
            raise ValueError("replay snapshots must have strictly increasing available_at values")
        self._snapshots = tuple(copied)
        self._available_times = tuple(available_times)

    def fetch_snapshot(self, *, as_of: datetime | None = None) -> NormalizedSnapshot:
        if as_of is None:
            return self._snapshots[-1]
        as_of = _utc(as_of, "as_of")
        index = bisect_right(self._available_times, as_of) - 1
        if index < 0:
            first = self._snapshots[0]
            return NormalizedSnapshot(
                metadata=DataSnapshotMetadata(
                    source_kind=first.metadata.source_kind,
                    instrument_or_topic=first.metadata.instrument_or_topic,
                    received_at=as_of,
                    available_at=as_of,
                    quality=DataQualityStatus.UNAVAILABLE,
                    provenance=first.metadata.provenance,
                ),
                values={
                    "source_id": first.metadata.provenance.source if first.metadata.provenance else "replay-fixture",
                    "error_class": "pit_unavailable",
                    "error_detail": "no_snapshot_available_at_or_before_as_of",
                },
            )
        return self._snapshots[index]


__all__ = ["FIXTURE_FORMAT_VERSION", "ReplayFixtureDataSource", "SnapshotFixtureCodec"]
