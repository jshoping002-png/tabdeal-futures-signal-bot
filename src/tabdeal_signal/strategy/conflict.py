from __future__ import annotations

from enum import Enum

from tabdeal_signal.domain.contracts import DecisionStatus, Direction, SideDecision


class ConflictPolicy(str, Enum):
    """Explicit policy required when LONG and SHORT are both eligible."""

    BLOCK_BOTH = "BLOCK_BOTH"


def apply_conflict_gate(
    long_decision: SideDecision,
    short_decision: SideDecision,
    *,
    policy: ConflictPolicy,
) -> tuple[SideDecision, SideDecision]:
    """Apply the sole LONG/SHORT comparison boundary deterministically."""
    if long_decision.direction is not Direction.LONG:
        raise ValueError("long_decision must declare LONG direction")
    if short_decision.direction is not Direction.SHORT:
        raise ValueError("short_decision must declare SHORT direction")

    if not (
        long_decision.status is DecisionStatus.SIGNAL
        and short_decision.status is DecisionStatus.SIGNAL
    ):
        return long_decision, short_decision

    if policy is ConflictPolicy.BLOCK_BOTH:
        return (
            SideDecision(Direction.LONG, DecisionStatus.BLOCKED, "CONFLICT_LONG_SHORT"),
            SideDecision(Direction.SHORT, DecisionStatus.BLOCKED, "CONFLICT_LONG_SHORT"),
        )

    raise ValueError("unsupported conflict policy")
