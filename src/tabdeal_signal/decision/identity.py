from __future__ import annotations

import hashlib

from tabdeal_signal.domain.contracts import Direction, SideDecision


IDENTITY_VERSION = "identity-v1"


def build_signal_id(*, snapshot_id: str, config_version: str, decision: SideDecision) -> str:
    """Build the deterministic logical identity for one qualified signal."""
    if not isinstance(snapshot_id, str) or not snapshot_id.strip():
        raise ValueError("snapshot_id is required")
    if not isinstance(config_version, str) or not config_version.strip():
        raise ValueError("config_version is required")
    if not isinstance(decision, SideDecision):
        raise ValueError("decision must be a SideDecision")
    if decision.status.value != "SIGNAL":
        raise ValueError("signal identity requires a SIGNAL decision")
    if decision.direction not in (Direction.LONG, Direction.SHORT):
        raise ValueError("unsupported signal direction")

    canonical = "|".join(
        (
            IDENTITY_VERSION,
            snapshot_id,
            config_version,
            decision.direction.value,
            decision.reason_code,
        )
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


__all__ = ["IDENTITY_VERSION", "build_signal_id"]
