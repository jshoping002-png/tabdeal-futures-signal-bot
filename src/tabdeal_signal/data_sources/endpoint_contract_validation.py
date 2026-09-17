"""Structural validation for endpoint contracts of existing source families.

This validates only the endpoint catalog already supported by source-verification
reports. It never invents unresolved paths and never enables authenticated access.
"""
from __future__ import annotations

from dataclasses import dataclass

from .endpoint_contracts import (
    EndpointExactness,
    VERIFIED_ENDPOINT_CONTRACTS,
)
from .source_access import VERIFIED_SOURCE_ACCESS_SPECS


_ALLOWED_METHODS = {"GET", "POST", "JSON-RPC"}


@dataclass(frozen=True, slots=True)
class EndpointValidationResult:
    source_id: str
    contract_count: int
    exact_count: int
    base_path_count: int
    runtime_configured_count: int
    valid: bool
    errors: tuple[str, ...]


def _validate_source(source_id: str) -> EndpointValidationResult:
    errors: list[str] = []
    contracts = tuple(item for item in VERIFIED_ENDPOINT_CONTRACTS if item.source_id == source_id)
    spec = next(item for item in VERIFIED_SOURCE_ACCESS_SPECS if item.source_id == source_id)

    exact = sum(item.exactness is EndpointExactness.EXACT for item in contracts)
    base = sum(item.exactness is EndpointExactness.BASE_PATH for item in contracts)
    runtime = sum(item.exactness is EndpointExactness.RUNTIME_CONFIGURED for item in contracts)

    if not contracts:
        errors.append("endpoint contract list is empty")
    if not spec.reports:
        errors.append("source report linkage is empty")

    seen_operations: set[tuple[str, str]] = set()
    for contract in contracts:
        operation_key = (contract.operation, contract.method)
        if operation_key in seen_operations:
            errors.append(f"duplicate endpoint operation: {contract.operation} {contract.method}")
        seen_operations.add(operation_key)

        if contract.method not in _ALLOWED_METHODS:
            errors.append(f"unsupported method: {contract.method}")
        if contract.auth_required:
            errors.append(f"authenticated endpoint is not allowed: {contract.operation}")
        if contract.exactness is EndpointExactness.EXACT and not contract.path:
            errors.append(f"exact endpoint has no path: {contract.operation}")
        elif contract.exactness is EndpointExactness.BASE_PATH and (
            not contract.path or not contract.path.endswith("/")
        ):
            errors.append(f"base-path endpoint is not slash-terminated: {contract.operation}")
        elif contract.exactness is EndpointExactness.RUNTIME_CONFIGURED and contract.path is not None:
            errors.append(f"runtime-configured endpoint has an invented path: {contract.operation}")
        if contract.evidence_report not in spec.reports:
            errors.append(
                f"endpoint evidence report is not linked to source reports: {contract.evidence_report}"
            )

    return EndpointValidationResult(
        source_id=source_id,
        contract_count=len(contracts),
        exact_count=exact,
        base_path_count=base,
        runtime_configured_count=runtime,
        valid=not errors,
        errors=tuple(errors),
    )


def validate_endpoint_catalog() -> tuple[EndpointValidationResult, ...]:
    """Validate every existing source family's endpoint contracts."""
    source_ids = tuple(spec.source_id for spec in VERIFIED_SOURCE_ACCESS_SPECS)
    contract_source_ids = tuple(dict.fromkeys(item.source_id for item in VERIFIED_ENDPOINT_CONTRACTS))
    if set(contract_source_ids) != set(source_ids):
        raise ValueError("endpoint catalog source IDs do not match source access IDs")

    results = tuple(_validate_source(source_id) for source_id in source_ids)
    errors = [
        f"{result.source_id}: {error}"
        for result in results
        if not result.valid
        for error in result.errors
    ]
    if errors:
        raise ValueError("; ".join(errors))
    return results


def endpoint_catalog_counts() -> dict[str, int]:
    """Return counts after validating the complete existing endpoint catalog."""
    results = validate_endpoint_catalog()
    return {
        "source_families": len(results),
        "contracts": sum(result.contract_count for result in results),
        "exact": sum(result.exact_count for result in results),
        "base_path": sum(result.base_path_count for result in results),
        "runtime_configured": sum(result.runtime_configured_count for result in results),
        "invalid_source_families": sum(not result.valid for result in results),
    }


__all__ = [
    "EndpointValidationResult",
    "endpoint_catalog_counts",
    "validate_endpoint_catalog",
]
