"""Derived operational manifest for the existing source families in reports 001-2040."""
from __future__ import annotations

from dataclasses import dataclass

from .endpoint_contracts import EndpointExactness, endpoint_contracts_for
from .source_access import (
    SourceLifecycle,
    SourceAccessSpec,
    VERIFIED_SOURCE_ACCESS_SPECS,
)


@dataclass(frozen=True, slots=True)
class SourceOperationalManifest:
    source_id: str
    reports: tuple[str, ...]
    lifecycle: SourceLifecycle
    adapter_classes: tuple[str, ...]
    endpoint_contract_count: int
    exact_endpoint_count: int
    base_path_count: int
    runtime_configured_count: int
    runtime_endpoint_required: bool

    @property
    def live_verified(self) -> bool:
        return self.lifecycle is SourceLifecycle.LIVE_VERIFIED

    @property
    def production_ready(self) -> bool:
        return self.lifecycle is SourceLifecycle.PRODUCTION_READY

    @property
    def active(self) -> bool:
        return self.lifecycle is SourceLifecycle.ACTIVE


def _manifest_for(spec: SourceAccessSpec) -> SourceOperationalManifest:
    contracts = endpoint_contracts_for(spec.source_id)
    exact = sum(item.exactness is EndpointExactness.EXACT for item in contracts)
    base = sum(item.exactness is EndpointExactness.BASE_PATH for item in contracts)
    runtime = sum(item.exactness is EndpointExactness.RUNTIME_CONFIGURED for item in contracts)
    return SourceOperationalManifest(
        source_id=spec.source_id,
        reports=spec.reports,
        lifecycle=spec.lifecycle,
        adapter_classes=spec.adapter_classes,
        endpoint_contract_count=len(contracts),
        exact_endpoint_count=exact,
        base_path_count=base,
        runtime_configured_count=runtime,
        runtime_endpoint_required=base > 0 or runtime > 0,
    )


SOURCE_OPERATIONAL_MANIFEST: tuple[SourceOperationalManifest, ...] = tuple(
    _manifest_for(spec) for spec in VERIFIED_SOURCE_ACCESS_SPECS
)


def operational_manifest_for(source_id: str) -> SourceOperationalManifest:
    if not isinstance(source_id, str) or not source_id.strip():
        raise ValueError("source_id must be non-empty")
    normalized = source_id.strip()
    for item in SOURCE_OPERATIONAL_MANIFEST:
        if item.source_id == normalized:
            return item
    raise KeyError(normalized)


def operational_manifest_counts() -> dict[str, int]:
    return {
        "source_families": len(SOURCE_OPERATIONAL_MANIFEST),
        "adapter_built": sum(item.lifecycle is SourceLifecycle.ADAPTER_BUILT for item in SOURCE_OPERATIONAL_MANIFEST),
        "live_verified": sum(item.live_verified for item in SOURCE_OPERATIONAL_MANIFEST),
        "production_ready": sum(item.production_ready for item in SOURCE_OPERATIONAL_MANIFEST),
        "active": sum(item.active for item in SOURCE_OPERATIONAL_MANIFEST),
        "exact_endpoint_contracts": sum(item.exact_endpoint_count for item in SOURCE_OPERATIONAL_MANIFEST),
        "base_path_contracts": sum(item.base_path_count for item in SOURCE_OPERATIONAL_MANIFEST),
        "runtime_configured_contracts": sum(item.runtime_configured_count for item in SOURCE_OPERATIONAL_MANIFEST),
    }


__all__ = [
    "SOURCE_OPERATIONAL_MANIFEST",
    "SourceOperationalManifest",
    "operational_manifest_counts",
    "operational_manifest_for",
]
