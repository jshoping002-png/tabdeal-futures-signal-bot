"""Structural validation for runtime endpoint configuration of existing sources.

This validates only configuration consistency. It never contacts providers, invents
endpoints, or promotes a source to live, production-ready, or active status.
"""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from .endpoint_contracts import EndpointExactness, VERIFIED_ENDPOINT_CONTRACTS
from .runtime_config import (
    KNOWN_RUNTIME_SOURCE_HOSTS,
    RUNTIME_CONFIGURED_SOURCE_IDS,
    explicit_runtime_endpoint_config,
    runtime_endpoint_config,
)
from .source_access import VERIFIED_SOURCE_ACCESS_SPECS


@dataclass(frozen=True, slots=True)
class RuntimeConfigValidationResult:
    source_id: str
    runtime_contract_count: int
    known_host_count: int
    requires_explicit_host: bool
    valid: bool
    errors: tuple[str, ...]


def _runtime_source_ids_from_contracts() -> set[str]:
    return {
        item.source_id
        for item in VERIFIED_ENDPOINT_CONTRACTS
        if item.exactness is EndpointExactness.RUNTIME_CONFIGURED
    }


def _validate_source(source_id: str) -> RuntimeConfigValidationResult:
    errors: list[str] = []
    runtime_contract_count = sum(
        item.source_id == source_id and item.exactness is EndpointExactness.RUNTIME_CONFIGURED
        for item in VERIFIED_ENDPOINT_CONTRACTS
    )
    known_hosts = KNOWN_RUNTIME_SOURCE_HOSTS.get(source_id, ())
    requires_explicit_host = not bool(known_hosts)

    if runtime_contract_count != 1:
        errors.append(f"expected exactly one runtime-configured endpoint contract, got {runtime_contract_count}")

    if len(known_hosts) != len(set(known_hosts)):
        errors.append("known runtime hosts contain duplicates")

    for host in known_hosts:
        parsed = urlparse(f"https://{host}")
        if parsed.hostname != host.lower() or parsed.path or parsed.query or parsed.fragment:
            errors.append(f"known runtime host is not a bare hostname: {host}")

    if requires_explicit_host:
        with_error = False
        try:
            runtime_endpoint_config(source_id, "https://example.invalid/validation")
        except ValueError:
            with_error = True
        except Exception as exc:
            errors.append(f"default runtime host policy raised unexpected error: {type(exc).__name__}: {exc}")
        if not with_error:
            errors.append("source without a known host must require explicit runtime host configuration")
    else:
        for host in known_hosts:
            try:
                config = runtime_endpoint_config(source_id, f"https://{host}/__validation__")
                if config.source_id != source_id:
                    errors.append("runtime config returned wrong source ID")
            except (ValueError, KeyError) as exc:
                errors.append(f"known host rejected by runtime config: {host}: {exc}")

    return RuntimeConfigValidationResult(
        source_id=source_id,
        runtime_contract_count=runtime_contract_count,
        known_host_count=len(known_hosts),
        requires_explicit_host=requires_explicit_host,
        valid=not errors,
        errors=tuple(errors),
    )


def validate_runtime_configuration_catalog() -> tuple[RuntimeConfigValidationResult, ...]:
    """Validate every existing runtime-configured source without network access."""
    known_source_ids = {spec.source_id for spec in VERIFIED_SOURCE_ACCESS_SPECS}
    configured_source_ids = set(RUNTIME_CONFIGURED_SOURCE_IDS)
    contract_source_ids = _runtime_source_ids_from_contracts()

    if configured_source_ids != contract_source_ids:
        raise ValueError("runtime configuration IDs do not match runtime-configured endpoint contract IDs")
    if not configured_source_ids.issubset(known_source_ids):
        raise ValueError("runtime configuration contains unknown source IDs")

    results = tuple(_validate_source(source_id) for source_id in RUNTIME_CONFIGURED_SOURCE_IDS)
    errors = [
        f"{result.source_id}: {error}"
        for result in results
        if not result.valid
        for error in result.errors
    ]
    if errors:
        raise ValueError("; ".join(errors))
    return results


def runtime_configuration_counts() -> dict[str, int]:
    """Return counts after validating all existing runtime source configurations."""
    results = validate_runtime_configuration_catalog()
    return {
        "runtime_sources": len(results),
        "known_host_sources": sum(not result.requires_explicit_host for result in results),
        "explicit_host_sources": sum(result.requires_explicit_host for result in results),
        "runtime_endpoint_contracts": sum(result.runtime_contract_count for result in results),
        "invalid_sources": sum(not result.valid for result in results),
    }


__all__ = [
    "RuntimeConfigValidationResult",
    "runtime_configuration_counts",
    "validate_runtime_configuration_catalog",
]
