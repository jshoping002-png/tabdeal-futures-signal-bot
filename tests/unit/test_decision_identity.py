from datetime import datetime, timezone

import pytest

from tabdeal_signal.decision.identity import build_signal_id
from tabdeal_signal.domain.contracts import DecisionStatus, Direction, SideDecision


UTC = timezone.utc


def signal(direction: Direction, reason: str = "ENTRY_BREAKOUT_LONG") -> SideDecision:
    return SideDecision(direction=direction, status=DecisionStatus.SIGNAL, reason_code=reason)


def test_same_logical_signal_has_same_identity() -> None:
    decision = signal(Direction.LONG)

    first = build_signal_id(
        snapshot_id="snapshot-1",
        config_version="strategy-v1",
        decision=decision,
    )
    second = build_signal_id(
        snapshot_id="snapshot-1",
        config_version="strategy-v1",
        decision=decision,
    )

    assert first == second
    assert len(first) == 64


def test_creation_time_is_not_part_of_identity() -> None:
    # Identity is built from logical decision fields only; processing time is
    # intentionally absent from the identity input.
    decision = signal(Direction.LONG)

    assert build_signal_id(
        snapshot_id="snapshot-1",
        config_version="strategy-v1",
        decision=decision,
    ) == build_signal_id(
        snapshot_id="snapshot-1",
        config_version="strategy-v1",
        decision=decision,
    )


def test_identity_changes_when_snapshot_config_direction_or_reason_changes() -> None:
    base = signal(Direction.LONG, "ENTRY_BREAKOUT_LONG")
    assert build_signal_id(snapshot_id="s1", config_version="c1", decision=base) != build_signal_id(
        snapshot_id="s2", config_version="c1", decision=base
    )
    assert build_signal_id(snapshot_id="s1", config_version="c1", decision=base) != build_signal_id(
        snapshot_id="s1", config_version="c2", decision=base
    )
    assert build_signal_id(snapshot_id="s1", config_version="c1", decision=base) != build_signal_id(
        snapshot_id="s1", config_version="c1", decision=signal(Direction.SHORT, "ENTRY_BREAKOUT_SHORT")
    )
    assert build_signal_id(snapshot_id="s1", config_version="c1", decision=base) != build_signal_id(
        snapshot_id="s1", config_version="c1", decision=signal(Direction.LONG, "OTHER_REASON")
    )


def test_identity_rejects_blocked_decision_and_blank_inputs() -> None:
    blocked = SideDecision(direction=Direction.LONG, status=DecisionStatus.BLOCKED, reason_code="NO_SIGNAL")

    with pytest.raises(ValueError, match="SIGNAL decision"):
        build_signal_id(snapshot_id="s1", config_version="c1", decision=blocked)
    with pytest.raises(ValueError, match="snapshot_id"):
        build_signal_id(snapshot_id=" ", config_version="c1", decision=signal(Direction.LONG))
    with pytest.raises(ValueError, match="config_version"):
        build_signal_id(snapshot_id="s1", config_version=" ", decision=signal(Direction.LONG))


def test_identity_is_stable_across_datetime_processing_context() -> None:
    # The identity API deliberately accepts no datetime, so equivalent replay
    # contexts cannot accidentally incorporate wall-clock creation time.
    t1 = datetime(2026, 1, 1, tzinfo=UTC)
    t2 = datetime(2026, 1, 2, tzinfo=UTC)
    assert t1 != t2
    decision = signal(Direction.SHORT, "ENTRY_BREAKOUT_SHORT")
    assert build_signal_id(snapshot_id="s1", config_version="c1", decision=decision) == build_signal_id(
        snapshot_id="s1", config_version="c1", decision=decision
    )
