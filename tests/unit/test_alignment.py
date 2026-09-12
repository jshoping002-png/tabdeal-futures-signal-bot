from datetime import datetime, timedelta, timezone

from tabdeal_signal.data.alignment import AlignmentPolicy, validate_alignment
from tabdeal_signal.data.series import TimeframeSpec
from tabdeal_signal.domain.contracts import Candle

UTC = timezone.utc


def candle(hour: int) -> Candle:
    start = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(hours=hour)
    return Candle("BTCUSDT", "4h", start, start + timedelta(hours=4), 100, 110, 90, 105, 1)


def policy() -> AlignmentPolicy:
    return AlignmentPolicy(TimeframeSpec.parse("4h"), datetime(2026, 1, 1, tzinfo=UTC))


def test_explicit_anchor_accepts_aligned_candles() -> None:
    assert validate_alignment((candle(0), candle(4), candle(8)), policy()) == ()


def test_boundary_mismatch_is_blocked() -> None:
    assert validate_alignment((candle(2),), policy()) == ("CANDLE_BOUNDARY_MISMATCH",)


def test_candle_before_anchor_is_blocked() -> None:
    shifted = AlignmentPolicy(TimeframeSpec.parse("4h"), datetime(2026, 1, 1, 4, tzinfo=UTC))
    assert validate_alignment((candle(0),), shifted) == ("CANDLE_BOUNDARY_MISMATCH",)


def test_anchor_is_not_inferred_from_candle_data() -> None:
    shifted = AlignmentPolicy(TimeframeSpec.parse("4h"), datetime(2026, 1, 1, 2, tzinfo=UTC))
    assert validate_alignment((candle(2),), shifted) == ()


def test_policy_requires_utc_anchor() -> None:
    try:
        AlignmentPolicy(TimeframeSpec.parse("4h"), datetime(2026, 1, 1))
    except ValueError as exc:
        assert "UTC" in str(exc)
    else:
        raise AssertionError("non-UTC alignment anchor must be rejected")


def test_timeframe_mismatch_is_blocked() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    one_hour = Candle("BTCUSDT", "1h", start, start + timedelta(hours=1), 100, 110, 90, 105, 1)
    assert validate_alignment((one_hour,), policy()) == ("CANDLE_BOUNDARY_MISMATCH",)


def test_reason_order_is_independent_of_candle_input_order() -> None:
    shifted = AlignmentPolicy(TimeframeSpec.parse("4h"), datetime(2026, 1, 1, 2, tzinfo=UTC))
    aligned = candle(2)
    mismatched_timeframe = Candle(
        "BTCUSDT",
        "1h",
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 1, 1, 1, tzinfo=UTC),
        100,
        110,
        90,
        105,
        1,
    )

    forward = validate_alignment((aligned, mismatched_timeframe), shifted)
    reverse = validate_alignment((mismatched_timeframe, aligned), shifted)

    assert forward == ("CANDLE_BOUNDARY_MISMATCH",)
    assert reverse == forward
