"""Deterministic readiness gates for existing source families in reports 001-2040.

Readiness is deliberately separate from lifecycle status: this module describes the
next gate that still has to be satisfied and never promotes a source by itself.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .operational_manifest import (
    SOURCE_OPERATIONAL_MANIFEST,
    SourceOperationalManifest,
    operational_manifest_for,
)
from .source_access import SourceLifecycle


class ReadinessGate(StrEnum):
    ADAPTER_BUILD = "adapter_build"
    ENDPOINT_CONFIGURATION = "endpoint_configuration"
    LIVE_VERIFICATION = "live_verification"
    PRODUCTION_VALIDATION = "production_validation"
    ACTIVATION = "activation"
    COMPLETE = "complete"


@dataclass(frozen=True, slots=True)
class SourceReadiness:
    source_id: str
    lifecycle: SourceLifecycle
    gate: ReadinessGate
    blockers: tuple[str, ...]

    @property
    def blocked(self) -> bool:
        return self.gate is not ReadinessGate.COMPLETE


def _readiness_for(manifest: SourceOperationalManifest) -> SourceReadiness:
    if manifest.lifecycle.rank < SourceLifecycle.ADAPTER_BUILT.rank:
        return SourceReadiness(
            source_id=manifest.source_id,
            lifecycle=manifest.lifecycle,
            gate=ReadinessGate.ADAPTER_BUILD,
            blockers=("adapter_implementation",),
        )

    if manifest.runtime_endpoint_required:
        return SourceReadiness(
            source_id=manifest.source_id,
            lifecycle=manifest.lifecycle,
            gate=ReadinessGate.ENDPOINT_CONFIGURATION,
            blockers=("endpoint_contract_resolution",),
        )

    if manifest.lifecycle.rank < SourceLifecycle.LIVE_VERIFIED.rank:
        return SourceReadiness(
            source_id=manifest.source_id,
            lifecycle=manifest.lifecycle,
            gate=ReadinessGate.LIVE_VERIFICATION,
            blockers=("live_operational_verification",),
        )

    if manifest.lifecycle.rank < SourceLifecycle.PRODUCTION_READY.rank:
        return SourceReadiness(
            source_id=manifest.source_id,
            lifecycle=manifest.lifecycle,
            gate=ReadinessGate.PRODUCTION_VALIDATION,
            blockers=("production_validation",),
        )

    if manifest.lifecycle.rank < SourceLifecycle.ACTIVE.rank:
        return SourceReadiness(
            source_id=manifest.source_id,
            lifecycle=manifest.lifecycle,
            gate=ReadinessGate.ACTIVATION,
            blockers=("explicit_activation",),
        )

    return SourceReadiness(
        source_id=manifest.source_id,
        lifecycle=manifest.lifecycle,
        gate=ReadinessGate.COMPLETE,
        blockers=(),
    )


def source_readiness_for(source_id: str) -> SourceReadiness:
    """Return the next deterministic readiness gate for one existing source."""
    return _readiness_for(operational_manifest_for(source_id))


def all_source_readiness() -> tuple[SourceReadiness, ...]:
    """Return readiness for the complete existing 001-2040 source catalog."""
    return tuple(_readiness_for(item) for item in SOURCE_OPERATIONAL_MANIFEST)


def source_readiness_counts() -> dict[str, int]:
    """Return counts by next readiness gate for the existing source catalog."""
    readiness = all_source_readiness()
    return {
        gate.value: sum(item.gate is gate for item in readiness)
        for gate in ReadinessGate
    }


__all__ = [
    "ReadinessGate",
    "SourceReadiness",
    "all_source_readiness",
    "source_readiness_counts",
    "source_readiness_for",
]
