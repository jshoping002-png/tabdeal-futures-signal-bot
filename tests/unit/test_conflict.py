from tabdeal_signal.domain.contracts import DecisionStatus, Direction, SideDecision
from tabdeal_signal.strategy.conflict import apply_conflict_gate


def decision(direction: Direction, status: DecisionStatus, reason: str) -> SideDecision:
    return SideDecision(direction, status, reason)


class StubResolver:
    def __init__(self) -> None:
        self.calls = 0

    def resolve(self, long_decision, short_decision):
        self.calls += 1
        return (
            SideDecision(Direction.LONG, DecisionStatus.BLOCKED, "EXPLICIT_CONFLICT_POLICY"),
            SideDecision(Direction.SHORT, DecisionStatus.BLOCKED, "EXPLICIT_CONFLICT_POLICY"),
        )


def test_non_conflicting_sides_pass_unchanged_without_calling_resolver():
    resolver = StubResolver()
    long = decision(Direction.LONG, DecisionStatus.SIGNAL, "LONG_OK")
    short = decision(Direction.SHORT, DecisionStatus.BLOCKED, "SHORT_BLOCKED")

    result_long, result_short = apply_conflict_gate(long, short, resolver=resolver)

    assert result_long == long
    assert result_short == short
    assert resolver.calls == 0


def test_simultaneous_long_and_short_are_delegated_to_explicit_resolver():
    resolver = StubResolver()
    result_long, result_short = apply_conflict_gate(
        decision(Direction.LONG, DecisionStatus.SIGNAL, "LONG_OK"),
        decision(Direction.SHORT, DecisionStatus.SIGNAL, "SHORT_OK"),
        resolver=resolver,
    )

    assert result_long.status is DecisionStatus.BLOCKED
    assert result_short.status is DecisionStatus.BLOCKED
    assert result_long.reason_code == "EXPLICIT_CONFLICT_POLICY"
    assert result_short.reason_code == "EXPLICIT_CONFLICT_POLICY"
    assert resolver.calls == 1


def test_wrong_direction_is_rejected():
    long = decision(Direction.SHORT, DecisionStatus.SIGNAL, "WRONG")
    short = decision(Direction.SHORT, DecisionStatus.SIGNAL, "SHORT_OK")

    try:
        apply_conflict_gate(long, short, resolver=StubResolver())
    except ValueError as exc:
        assert "long_decision" in str(exc)
    else:
        raise AssertionError("expected ValueError")
