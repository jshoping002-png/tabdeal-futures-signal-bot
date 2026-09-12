from __future__ import annotations

from typing import Protocol

from tabdeal_signal.domain.contracts import Direction, SideDecision


class ConflictResolver(Protocol):
    """Caller-supplied policy for the case where both sides signal."""

    def resolve(
        self,
        long_decision: SideDecision,
        short_decision: SideDecision,
    ) -> tuple[SideDecision, SideDecision]:
        ...


def apply_conflict_gate(
    long_decision: SideDecision,
    short_decision: SideDecision,
    *,
    resolver: ConflictResolver,
) -> tuple[SideDecision, SideDecision]:
    """Compare LONG/SHORT only at this boundary; conflict policy is injected."""
    if long_decision.direction is not Direction.LONG:
        raise ValueError("long_decision must declare LONG direction")
    if short_decision.direction is not Direction.SHORT:
        raise ValueError("short_decision must declare SHORT direction")

    if long_decision.status.value != "SIGNAL" or short_decision.status.value != "SIGNAL":
        return long_decision, short_decision

    return resolver.resolve(long_decision, short_decision)
