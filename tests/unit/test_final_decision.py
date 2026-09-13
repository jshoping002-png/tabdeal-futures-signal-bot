from datetime import datetime, timezone

import pytest

from tabdeal_signal.decision.final import FinalDecision, resolve_final_decision
from tabdeal_signal.domain.contracts import DecisionStatus, Direction, SideDecision, SignalDecision

UTC = timezone.utc
CREATED = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def side(direction: Direction, status: DecisionStatus, reason: str) -> SideDecision:
    return SideDecision(direction=direction, status=status, reason_code=reason)


def resolve(long_status, short_status):
    return resolve_final_decision(
        long_decision=side(Direction.LONG, long_status, "LONG_OK"),
        short_decision=side(Direction.SHORT, short_status, "SHORT_OK"),
        signal_id="signal-1",
        created_at=CREATED,
        snapshot_id="snapshot-1",
        config_version="config-1",
    )


def test_long_only_produces_signal() -> None:
    result = resolve(DecisionStatus.SIGNAL, DecisionStatus.BLOCKED)

    assert result.status is DecisionStatus.SIGNAL
    assert isinstance(result.signal, SignalDecision)
    assert result.signal.direction is Direction.LONG
    assert result.signal.reason_code == "LONG_OK"


def test_short_only_produces_signal() -> None:
    result = resolve(DecisionStatus.BLOCKED, DecisionStatus.SIGNAL)

    assert result.status is DecisionStatus.SIGNAL
    assert result.signal is not None
    assert result.signal.direction is Direction.SHORT


def test_both_signals_are_blocked_without_direction_priority() -> None:
    result = resolve(DecisionStatus.SIGNAL, DecisionStatus.SIGNAL)

    assert result == FinalDecision(DecisionStatus.BLOCKED, reason_code="CONFLICT_BOTH_DIRECTIONS")


def test_no_signal_is_blocked() -> None:
    result = resolve(DecisionStatus.BLOCKED, DecisionStatus.BLOCKED)

    assert result == FinalDecision(DecisionStatus.BLOCKED, reason_code="NO_SIGNAL")


def test_blocked_final_decision_cannot_carry_signal() -> None:
    with pytest.raises(ValueError, match="BLOCKED cannot contain"):
        FinalDecision(
            status=DecisionStatus.BLOCKED,
            signal=SignalDecision(
                signal_id="signal-1",
                direction=Direction.LONG,
                created_at=CREATED,
                snapshot_id="snapshot-1",
                config_version="config-1",
                reason_code="LONG_OK",
            ),
            reason_code="NO_SIGNAL",
        )


def test_signal_final_decision_requires_signal() -> None:
    with pytest.raises(ValueError, match="SIGNAL requires"):
        FinalDecision(status=DecisionStatus.SIGNAL)


def test_final_resolution_rejects_wrong_side_directions() -> None:
    with pytest.raises(ValueError, match="directions must be LONG and SHORT"):
        resolve_final_decision(
            long_decision=side(Direction.SHORT, DecisionStatus.SIGNAL, "WRONG"),
            short_decision=side(Direction.SHORT, DecisionStatus.BLOCKED, "BLOCKED"),
            signal_id="signal-1",
            created_at=CREATED,
            snapshot_id="snapshot-1",
            config_version="config-1",
        )
