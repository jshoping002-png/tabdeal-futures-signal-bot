from datetime import datetime, timezone

import pytest

from tabdeal_signal.domain.contracts import Direction
from tabdeal_signal.strategy.engine import _latest_bos_and_choch


def test_latest_bos_and_choch_returns_explicit_none_pair_when_context_is_empty():
    result = _latest_bos_and_choch((), datetime(2026, 1, 1, tzinfo=timezone.utc), Direction.LONG)

    assert result == (None, None)
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_latest_bos_and_choch_rejects_naive_reference_time_before_processing():
    with pytest.raises(ValueError, match="timezone-aware"):
        _latest_bos_and_choch((), datetime(2026, 1, 1), Direction.LONG)
