from datetime import datetime, timedelta, timezone

from tabdeal_signal.data.contracts import MarketSnapshot
from tabdeal_signal.decision.final import FinalDecision
from tabdeal_signal.decision.pipeline import evaluate_final_decision
from tabdeal_signal.domain.contracts import (
    Candle,
    DecisionContext,
    DecisionStatus,
    Direction,
)
from tabdeal_signal.risk.contracts import RiskEvaluation, RiskEvaluationRequest
from tabdeal_signal.strategy.conflict import BlockOnConflictResolver
from tabdeal_signal.strategy.contracts import StrategyEvaluation, StrategyEvaluationRequest
from tabdeal_signal.strategy.isolation import IsolatedSideEvaluators

UTC = timezone.utc
OPEN = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
CLOSE = OPEN + timedelta(hours=1)
REFERENCE = CLOSE + timedelta(minutes=1)
CREATED = REFERENCE


class FakeStrategyEvaluator:
    def __init__(self, direction: Direction, eligible: bool) -> None:
        self.direction = direction
        self.eligible = eligible

    def evaluate(self, request: StrategyEvaluationRequest) -> StrategyEvaluation:
        return StrategyEvaluation(
            direction=self.direction,
            eligible=self.eligible,
            reason_code=f"{self.direction.value}_STRATEGY",
        )


class FakeRiskEvaluator:
    def __init__(self, direction: Direction, allowed: bool) -> None:
        self.direction = direction
        self.allowed = allowed
        self.calls = 0

    def evaluate(self, request: RiskEvaluationRequest) -> RiskEvaluation:
        self.calls += 1
        return RiskEvaluation(
            direction=request.decision.direction,
            allowed=self.allowed,
            reason_code=f"{self.direction.value}_RISK",
        )


def context_and_snapshot() -> tuple[DecisionContext, MarketSnapshot]:
    candle = Candle(
        symbol="BTCUSDT",
        timeframe="1h",
        open_time=OPEN,
        close_time=CLOSE,
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.5,
        volume=1.0,
    )
    snapshot = MarketSnapshot(
        snapshot_id="snapshot-1",
        source_id="test-source",
        reference_time=REFERENCE,
        candles=(candle,),
    )
    context = DecisionContext(
        decision_time=REFERENCE,
        reference_time=REFERENCE,
        snapshot_id="snapshot-1",
        config_version="config-1",
    )
    return context, snapshot


def run_pipeline(long_ok: bool, short_ok: bool, long_risk: bool = True, short_risk: bool = True):
    context, snapshot = context_and_snapshot()
    long_risk_evaluator = FakeRiskEvaluator(Direction.LONG, long_risk)
    short_risk_evaluator = FakeRiskEvaluator(Direction.SHORT, short_risk)
    result = evaluate_final_decision(
        context=context,
        snapshot=snapshot,
        evaluators=IsolatedSideEvaluators(
            long_evaluator=FakeStrategyEvaluator(Direction.LONG, long_ok),
            short_evaluator=FakeStrategyEvaluator(Direction.SHORT, short_ok),
        ),
        conflict_resolver=BlockOnConflictResolver(),
        long_risk_evaluator=long_risk_evaluator,
        short_risk_evaluator=short_risk_evaluator,
        signal_id="signal-1",
        created_at=CREATED,
    )
    return result, long_risk_evaluator, short_risk_evaluator


def test_pipeline_resolves_long_signal_after_gates() -> None:
    result, long_risk, short_risk = run_pipeline(True, False)

    assert result.status is DecisionStatus.SIGNAL
    assert result.signal is not None
    assert result.signal.direction is Direction.LONG
    assert result.signal.snapshot_id == "snapshot-1"
    assert result.signal.config_version == "config-1"
    assert long_risk.calls == 1
    assert short_risk.calls == 0


def test_pipeline_resolves_short_signal_after_gates() -> None:
    result, long_risk, short_risk = run_pipeline(False, True)

    assert result.status is DecisionStatus.SIGNAL
    assert result.signal is not None
    assert result.signal.direction is Direction.SHORT
    assert long_risk.calls == 0
    assert short_risk.calls == 1


def test_pipeline_blocks_both_strategy_signals_at_conflict_gate() -> None:
    result, long_risk, short_risk = run_pipeline(True, True)

    assert result == FinalDecision(DecisionStatus.BLOCKED, reason_code="CONFLICT_BOTH_DIRECTIONS")
    assert long_risk.calls == 0
    assert short_risk.calls == 0


def test_pipeline_blocks_when_risk_rejects_only_candidate() -> None:
    result, long_risk, short_risk = run_pipeline(True, False, long_risk=False)

    assert result == FinalDecision(DecisionStatus.BLOCKED, reason_code="NO_SIGNAL")
    assert long_risk.calls == 1
    assert short_risk.calls == 0


def test_pipeline_blocks_when_neither_strategy_side_is_eligible() -> None:
    result, long_risk, short_risk = run_pipeline(False, False)

    assert result == FinalDecision(DecisionStatus.BLOCKED, reason_code="NO_SIGNAL")
    assert long_risk.calls == 0
    assert short_risk.calls == 0
