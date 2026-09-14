from __future__ import annotations

from dataclasses import dataclass

from tabdeal_signal.data.contracts import MarketDataSource, MarketSnapshot, SnapshotRequest, validate_snapshot_request
from tabdeal_signal.data.validation import ValidationReport, validate_snapshot


@dataclass(frozen=True, slots=True)
class IngestionResult:
    snapshot: MarketSnapshot
    validation: ValidationReport


class MarketDataIngestionError(ValueError):
    """Raised when a source response cannot safely enter the decision pipeline."""


def ingest(source: MarketDataSource, request: SnapshotRequest) -> IngestionResult:
    """Receive one point-in-time snapshot and fail closed on any contract violation."""
    if not isinstance(request, SnapshotRequest):
        raise MarketDataIngestionError("request must be a SnapshotRequest")
    if not isinstance(source, MarketDataSource):
        raise MarketDataIngestionError("source must implement MarketDataSource")

    snapshot = source.snapshot(request)
    if not isinstance(snapshot, MarketSnapshot):
        raise MarketDataIngestionError("source returned an invalid snapshot type")
    if snapshot.source_id != source.source_id:
        raise MarketDataIngestionError("source identity mismatch")

    scope_reasons = validate_snapshot_request(request, snapshot)
    if scope_reasons:
        raise MarketDataIngestionError("snapshot scope rejected: " + ",".join(scope_reasons))

    report = validate_snapshot(request, snapshot)
    if not report.valid:
        raise MarketDataIngestionError("snapshot validation failed: " + ",".join(issue.code for issue in report.issues))

    return IngestionResult(snapshot=snapshot, validation=report)
