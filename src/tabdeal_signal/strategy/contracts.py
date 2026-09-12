from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from tabdeal_signal.data.contracts import MarketSnapshot
from tabdeal_signal.domain.contracts import DecisionContext, DecisionStatus, Direction, SideDecision


@dataclass(frozen=True, slots=True)
class StrategyEvaluationRequest:
    context: DecisionContext
    snapshot: MarketSnapshot

    def __post_init__(self) -> None:
        if self.snapshot.reference_time != self.context.reference_time:
            raise ValueError("snapshot reference_time must match decision context")
        if self.snapshot.snapshot_id != self.context.snapshot_id:
            raise ValueError("snapshot_id must match decision context")


@dataclass(frozen=True, slots=True)
class StrategyEvaluation:
    direction: Direction
    eligible: bool
    reason_code: str

    def __post_init__(self) -> None:
        if not self.reason_code.strip():
            raise ValueError("reason_code is required")

    def to_side_decision(self) -> SideDecision:
        return SideDecision(
            direction=self.direction,
            status=DecisionStatus.SIGNAL if self.eligible else DecisionStatus.BLOCKED,
            reason_code=self.reason_code,
        )


class StrategyEvaluator(Protocol):
    """Pure strategy boundary: request in, one deterministic side result out."""

    direction: Direction

    def evaluate(self, request: StrategyEvaluationRequest) -> StrategyEvaluation:
        ...
