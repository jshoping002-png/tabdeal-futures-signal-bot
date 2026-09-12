from tabdeal_signal.domain.contracts import DecisionStatus, Direction, SideDecision
from tabdeal_signal.strategy.conflict import ConflictPolicy, apply_conflict_gate


def decision(direction: Direction, status: DecisionStatus, reason: str) -> SideDecision:
    return SideDecision(direction, status, reason)


def test_non_conflicting_sides_pass_unchanged():
    long = decision(Direction.LONG, DecisionStatus.SIGNAL, "LONG_OK")
    short = decision(Direction.SHORT, DecisionStatus.BLOCKED, "SHORT_BLOCKED")

    result_long, result_short = apply_conflict_gate(
        long, short, policy=ConflictPolicy.BLOCK_BOTH
    )

    assert result_long == long
    assert result_short == short


def test_simultaneous_long_and_short_are_blocked_explicitly():
    result_long, result_short = apply_conflict_gate(
        decision(Direction.LONG, DecisionStatus.SIGNAL, "LONG_OK"),
        decision(Direction.SHORT, DecisionStatus.SIGNAL, "SHORT_OK"),
        policy=ConflictPolicy.BLOCK_BOTH,
    )

    assert result_long == SideDecision(
        Direction.LONG, DecisionStatus.BLOCKED, "CONFLICT_LONG_SHORT"
    )
    assert result_short == SideDecision(
        Direction.SHORT, DecisionStatus.BLOCKED, "CONFLICT_LONG_SHORT"
    )


def test_wrong_direction_is_rejected():
    long = decision(Direction.SHORT, DecisionStatus.SIGNAL, "WRONG")
    short = decision(Direction.SHORT, DecisionStatus.SIGNAL, "SHORT_OK")

    try:
        apply_conflict_gate(long, short, policy=ConflictPolicy.BLOCK_BOTH)
    except ValueError as exc:
        assert "long_decision" in str(exc)
    else:
        raise AssertionError("expected ValueError")
