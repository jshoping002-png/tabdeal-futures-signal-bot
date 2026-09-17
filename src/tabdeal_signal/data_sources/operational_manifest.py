"""Derived operational manifest for the existing source families in reports 001-2040."""
from __future__ import annotations

from dataclasses import dataclass

from .adapter_catalog import VERIFIED_ADAPTER_BINDINGS, source_ids_with_adapters
from .endpoint_contracts import (
    EndpointExactness,
    VERIFIED_ENDPOINT_CONTRACTS,
    endpoint_contracts_for,
    source_ids_with_endpoint_contracts,
)
from .source_access import (
    SourceLifecycle,
    SourceAccessSpec,
    VERIFIED_SOURCE_ACCESS_SPECS,
    source_ids,
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


def validate_operational_manifest() -> None:
    """Fail closed when the source/access/adapter/endpoint catalogs drift apart."""
    errors: list[str] = []
    access_ids = source_ids()
    manifest_ids = tuple(item.source_id for item in SOURCE_OPERATIONAL_MANIFEST)
    adapter_ids = source_ids_with_adapters()
    endpoint_ids = source_ids_with_endpoint_contracts()

    if len(access_ids) != len(set(access_ids)):
        errors.append("source access catalog contains duplicate source IDs")
    if len(manifest_ids) != len(set(manifest_ids)):
        errors.append("operational manifest contains duplicate source IDs")
    if manifest_ids != access_ids:
        errors.append("operational manifest IDs do not match source access IDs")
    if set(adapter_ids) != set(access_ids):
        errors.append("adapter catalog source IDs do not match source access IDs")
    if set(endpoint_ids) != set(access_ids):
        errors.append("endpoint catalog source IDs do not match source access IDs")

    binding_pairs = {
        (binding.source_id, binding.class_name)
        for binding in VERIFIED_ADAPTER_BINDINGS
    }
    for spec in VERIFIED_SOURCE_ACCESS_SPECS:
        declared_pairs = {(spec.source_id, class_name) for class_name in spec.adapter_classes}
        if not spec.reports:
            errors.append(f"{spec.source_id}: report linkage is empty")
        if not spec.adapter_classes or not spec.adapter_scope:
            errors.append(f"{spec.source_id}: adapter lifecycle lacks class/scope")
        if not declared_pairs.issubset(binding_pairs):
            errors.append(f"{spec.source_id}: declared adapter class has no catalog binding")

        contracts = endpoint_contracts_for(spec.source_id)
        if not contracts:
            errors.append(f"{spec.source_id}: no endpoint contract")
        evidence_reports = {item.evidence_report for item in contracts}
        missing_reports = sorted(evidence_reports.difference(spec.reports))
        if missing_reports:
            errors.append(
                f"{spec.source_id}: endpoint evidence not linked to source reports {missing_reports}"
            )

    for item in SOURCE_OPERATIONAL_MANIFEST:
        contracts = endpoint_contracts_for(item.source_id)
        expected_exact = sum(item_.exactness is EndpointExactness.EXACT for item_ in contracts)
        expected_base = sum(item_.exactness is EndpointExactness.BASE_PATH for item_ in contracts)
        expected_runtime = sum(
            item_.exactness is EndpointExactness.RUNTIME_CONFIGURED for item_ in contracts
        )
        if item.endpoint_contract_count != len(contracts):
            errors.append(f"{item.source_id}: endpoint contract count drift")
        if item.exact_endpoint_count != expected_exact:
            errors.append(f"{item.source_id}: exact endpoint count drift")
        if item.base_path_count != expected_base:
            errors.append(f"{item.source_id}: base path count drift")
        if item.runtime_configured_count != expected_runtime:
            errors.append(f"{item.source_id}: runtime endpoint count drift")
        if item.runtime_endpoint_required != (expected_base > 0 or expected_runtime > 0):
            errors.append(f"{item.source_id}: runtime endpoint requirement drift")

    if errors:
        raise ValueError("; ".join(errors))


validate_operational_manifest()


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
    "validate_operational_manifest",
]
