from __future__ import annotations

from dataclasses import dataclass

from tabdeal_signal.domain.contracts import DecisionStatus, Direction, SideDecision, SignalDecision


@dataclass(frozen=True, slots=True)
class FinalDecision:
    """Deterministic final signal outcome after conflict and risk gates."""

    status: DecisionStatus
    signal: SignalDecision | None = None
    reason_code: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.status, DecisionStatus):
            raise ValueError("status must be a DecisionStatus")
        if self.status is DecisionStatus.SIGNAL:
            if not isinstance(self.signal, SignalDecision):
                raise ValueError("SIGNAL requires a SignalDecision")
            if self.reason_code:
                raise ValueError("SIGNAL cannot contain a blocking reason_code")
        else:
            if self.signal is not None:
                raise ValueError("BLOCKED cannot contain a SignalDecision")
            if not isinstance(self.reason_code, str) or not self.reason_code.strip():
                raise ValueError("BLOCKED requires a reason_code")


def resolve_final_decision(
    *,
    long_decision: SideDecision,
    short_decision: SideDecision,
    signal_id: str,
    created_at,
    snapshot_id: str,
    config_version: str,
) -> FinalDecision:
    """Resolve post-gate side decisions without inventing direction priority."""
    if not isinstance(long_decision, SideDecision) or not isinstance(short_decision, SideDecision):
        raise ValueError("side decisions must be SideDecision instances")
    if long_decision.direction is not Direction.LONG or short_decision.direction is not Direction.SHORT:
        raise ValueError("directions must be LONG and SHORT")

    long_signal = long_decision.status is DecisionStatus.SIGNAL
    short_signal = short_decision.status is DecisionStatus.SIGNAL

    if long_signal and short_signal:
        return FinalDecision(DecisionStatus.BLOCKED, reason_code="CONFLICT_BOTH_DIRECTIONS")
    if not long_signal and not short_signal:
        return FinalDecision(DecisionStatus.BLOCKED, reason_code="NO_SIGNAL")

    selected = long_decision if long_signal else short_decision
    signal = SignalDecision(
        signal_id=signal_id,
        direction=selected.direction,
        created_at=created_at,
        snapshot_id=snapshot_id,
        config_version=config_version,
        reason_code=selected.reason_code,
    )
    return FinalDecision(DecisionStatus.SIGNAL, signal=signal)
