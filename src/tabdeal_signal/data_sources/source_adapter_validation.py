"""Structural validation for the existing read-only source adapter catalog.

This validates importable adapter bindings without claiming live connectivity,
provider availability, or production readiness.
"""
from __future__ import annotations

from dataclasses import dataclass

from .adapter_catalog import (
    VERIFIED_ADAPTER_BINDINGS,
    adapter_bindings_for,
    resolve_adapter_class,
)
from .operational_manifest import operational_manifest_for
from .source_access import VERIFIED_SOURCE_ACCESS_SPECS


@dataclass(frozen=True, slots=True)
class AdapterValidationResult:
    source_id: str
    declared_adapter_count: int
    resolved_adapter_count: int
    binding_count: int
    valid: bool
    errors: tuple[str, ...]


def _validate_source(source_id: str) -> AdapterValidationResult:
    errors: list[str] = []
    spec = next(item for item in VERIFIED_SOURCE_ACCESS_SPECS if item.source_id == source_id)
    manifest = operational_manifest_for(source_id)
    bindings = adapter_bindings_for(source_id)
    resolved = 0

    if not spec.adapter_classes:
        errors.append("adapter_classes is empty")
    if not spec.adapter_scope:
        errors.append("adapter_scope is empty")
    if manifest.adapter_classes != spec.adapter_classes:
        errors.append("manifest adapter classes differ from source access")

    expected_pairs = {(source_id, class_name) for class_name in spec.adapter_classes}
    actual_pairs = {(item.source_id, item.class_name) for item in bindings}
    if actual_pairs != expected_pairs:
        errors.append("adapter bindings differ from source access")

    for binding in bindings:
        try:
            resolved_class = resolve_adapter_class(source_id, binding.class_name)
            if resolved_class.__name__ != binding.class_name:
                errors.append(f"resolved class name mismatch: {binding.class_name}")
            resolved += 1
        except (ImportError, LookupError, TypeError, ValueError) as exc:
            errors.append(f"adapter resolution failed for {binding.class_name}: {exc}")

    return AdapterValidationResult(
        source_id=source_id,
        declared_adapter_count=len(spec.adapter_classes),
        resolved_adapter_count=resolved,
        binding_count=len(bindings),
        valid=not errors and resolved == len(bindings),
        errors=tuple(errors),
    )


def validate_source_adapter_catalog() -> tuple[AdapterValidationResult, ...]:
    """Validate every existing source family's declared adapter bindings."""
    known_source_ids = {spec.source_id for spec in VERIFIED_SOURCE_ACCESS_SPECS}
    binding_source_ids = {binding.source_id for binding in VERIFIED_ADAPTER_BINDINGS}
    if binding_source_ids != known_source_ids:
        raise ValueError("adapter binding source IDs do not match source access IDs")
    results = tuple(_validate_source(item.source_id) for item in VERIFIED_SOURCE_ACCESS_SPECS)
    errors = [
        f"{result.source_id}: {error}"
        for result in results
        if not result.valid
        for error in result.errors
    ]
    if errors:
        raise ValueError("; ".join(errors))
    return results


def source_adapter_validation_counts() -> dict[str, int]:
    """Return structural validation counts after validating the full catalog."""
    results = validate_source_adapter_catalog()
    return {
        "source_families": len(results),
        "valid_source_families": sum(result.valid for result in results),
        "adapter_bindings": sum(result.binding_count for result in results),
        "resolved_adapters": sum(result.resolved_adapter_count for result in results),
        "invalid_source_families": sum(not result.valid for result in results),
    }


__all__ = [
    "AdapterValidationResult",
    "source_adapter_validation_counts",
    "validate_source_adapter_catalog",
]
