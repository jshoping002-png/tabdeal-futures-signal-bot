from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from tabdeal_signal.domain.contracts import DecisionContext, DecisionStatus, Direction, SideDecision


@dataclass(frozen=True, slots=True)
class RiskEvaluationRequest:
    context: DecisionContext
    decision: SideDecision

    def __post_init__(self) -> None:
        if not isinstance(self.context, DecisionContext):
            raise ValueError("context must be a DecisionContext")
        if not isinstance(self.decision, SideDecision):
            raise ValueError("decision must be a SideDecision")


@dataclass(frozen=True, slots=True)
class RiskEvaluation:
    direction: Direction
    allowed: bool
    reason_code: str

    def __post_init__(self) -> None:
        if not isinstance(self.direction, Direction):
            raise ValueError("direction must be a Direction")
        if not isinstance(self.allowed, bool):
            raise ValueError("allowed must be a bool")
        if not isinstance(self.reason_code, str) or not self.reason_code.strip():
            raise ValueError("reason_code is required")

    def to_side_decision(self, original: SideDecision) -> SideDecision:
        if original.direction is not self.direction:
            raise ValueError("risk evaluation direction must match decision direction")
        if original.status is DecisionStatus.BLOCKED:
            return original
        return SideDecision(
            direction=original.direction,
            status=DecisionStatus.SIGNAL if self.allowed else DecisionStatus.BLOCKED,
            reason_code=self.reason_code,
        )


class RiskEvaluator(Protocol):
    """Pure risk boundary; concrete risk rules are supplied by an explicit policy."""

    def evaluate(self, request: RiskEvaluationRequest) -> RiskEvaluation:
        ...
