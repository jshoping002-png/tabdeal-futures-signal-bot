from __future__ import annotations

from threading import RLock

from tabdeal_signal.data.contracts import (
    MarketDataSource,
    MarketSnapshot,
    SnapshotRequest,
    validate_snapshot_request,
)
from tabdeal_signal.data.validation import validate_snapshot


class InMemoryMarketDataSource(MarketDataSource):
    """Deterministic source adapter for tests and replay fixtures.

    It never creates, repairs, trims, or infers market data. A snapshot must be
    registered explicitly and must satisfy the same point-in-time validation
    applied to source responses.
    """

    def __init__(self, source_id: str) -> None:
        if not isinstance(source_id, str) or not source_id.strip():
            raise ValueError("source_id is required")
        self.source_id = source_id
        self._snapshots: dict[SnapshotRequest, MarketSnapshot] = {}
        self._lock = RLock()

    def register(self, request: SnapshotRequest, snapshot: MarketSnapshot) -> None:
        if not isinstance(request, SnapshotRequest):
            raise ValueError("request must be a SnapshotRequest")
        if not isinstance(snapshot, MarketSnapshot):
            raise ValueError("snapshot must be a MarketSnapshot")
        if snapshot.source_id != self.source_id:
            raise ValueError("snapshot source_id does not match source")
        scope_reasons = validate_snapshot_request(request, snapshot)
        if scope_reasons:
            raise ValueError("invalid snapshot request scope: " + ",".join(scope_reasons))
        report = validate_snapshot(request, snapshot)
        if not report.valid:
            raise ValueError("invalid snapshot: " + ",".join(issue.code for issue in report.issues))
        with self._lock:
            existing = self._snapshots.get(request)
            if existing is not None and existing != snapshot:
                raise ValueError("snapshot request already registered with different data")
            self._snapshots[request] = snapshot

    def snapshot(self, request: SnapshotRequest) -> MarketSnapshot:
        if not isinstance(request, SnapshotRequest):
            raise ValueError("request must be a SnapshotRequest")
        with self._lock:
            snapshot = self._snapshots.get(request)
        if snapshot is None:
            raise LookupError("market data unavailable for requested point-in-time scope")
        return snapshot
