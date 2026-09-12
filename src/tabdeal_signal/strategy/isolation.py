from __future__ import annotations

from dataclasses import dataclass

from tabdeal_signal.domain.contracts import Direction
from tabdeal_signal.strategy.contracts import StrategyEvaluation, StrategyEvaluationRequest, StrategyEvaluator


@dataclass(frozen=True, slots=True)
class IsolatedSideEvaluators:
    """Explicit LONG/SHORT evaluator boundary.

    Each side is evaluated independently from the same immutable request. A side
    evaluator never receives the other side's result.
    """

    long_evaluator: StrategyEvaluator
    short_evaluator: StrategyEvaluator

    def __post_init__(self) -> None:
        if self.long_evaluator.direction is not Direction.LONG:
            raise ValueError("long_evaluator must declare LONG direction")
        if self.short_evaluator.direction is not Direction.SHORT:
            raise ValueError("short_evaluator must declare SHORT direction")

    def evaluate_long(self, request: StrategyEvaluationRequest) -> StrategyEvaluation:
        return self.long_evaluator.evaluate(request)

    def evaluate_short(self, request: StrategyEvaluationRequest) -> StrategyEvaluation:
        return self.short_evaluator.evaluate(request)
