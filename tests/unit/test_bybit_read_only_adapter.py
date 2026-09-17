from datetime import datetime, timezone
from decimal import Decimal
import json

import pytest

from tabdeal_signal.data_sources.bybit import BybitOrderbookDataSource
from tabdeal_signal.data_sources.contracts import DataQualityStatus


class FakeTransport:
    def __init__(self, payload, received):
        self.payload = payload
        self.received = received
        self.calls = []

    def get(self, path, params, timeout_seconds):
        self.calls.append((path, params, timeout_seconds))
        return self.payload, self.received


BASE = {
    "retCode": 0,
    "retMsg": "OK",
    "result": {
        "s": "BTCUSDT",
        "b": [["101", "2"], ["100", "3"]],
        "a": [["102", "4"], ["103", "5"]],
        "ts": 1716863719031,
        "u": 230704,
        "seq": 1432604333,
        "cts": 1716863718905,
    },
}
NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_valid_snapshot_normalizes_and_preserves_timing():
    transport = FakeTransport(BASE, NOW)
    source = BybitOrderbookDataSource("btcusdt", transport=transport, clock=lambda: NOW)

    result = source.fetch_snapshot()

    assert result.metadata.quality is DataQualityStatus.VALID
    assert result.metadata.available_at == NOW
    assert result.values["bids"] == (
        (Decimal("101"), Decimal("2")),
        (Decimal("100"), Decimal("3")),
    )
    assert transport.calls[0][1] == {"category": "linear", "symbol": "BTCUSDT"}


def test_pit_rejects_snapshot_received_after_as_of():
    source = BybitOrderbookDataSource(
        "BTCUSDT", transport=FakeTransport(BASE, NOW), clock=lambda: NOW
    )

    result = source.fetch_snapshot(as_of=datetime(2025, 12, 31, tzinfo=timezone.utc))

    assert result.metadata.quality is DataQualityStatus.UNAVAILABLE
    assert result.values["error_class"] == "pit_unavailable"


def test_rate_limit_response_is_unavailable():
    payload = {"retCode": 10006, "retMsg": "Too many visits!", "result": {}}

    result = BybitOrderbookDataSource(
        "BTCUSDT", transport=FakeTransport(payload, NOW), clock=lambda: NOW
    ).fetch_snapshot()

    assert result.metadata.quality is DataQualityStatus.UNAVAILABLE
    assert result.values["error_class"] == "rate_limited"


def test_malformed_book_is_invalid():
    payload = json.loads(json.dumps(BASE))
    payload["result"]["a"] = [["103", "1"], ["102", "2"]]

    result = BybitOrderbookDataSource(
        "BTCUSDT", transport=FakeTransport(payload, NOW), clock=lambda: NOW
    ).fetch_snapshot()

    assert result.metadata.quality is DataQualityStatus.INVALID
    assert result.values["error_class"] == "schema_error"


def test_nonzero_provider_code_is_unavailable():
    payload = {"retCode": 10001, "retMsg": "provider failure", "result": {}}

    result = BybitOrderbookDataSource(
        "BTCUSDT", transport=FakeTransport(payload, NOW), clock=lambda: NOW
    ).fetch_snapshot()

    assert result.metadata.quality is DataQualityStatus.UNAVAILABLE
    assert result.values["error_class"] == "provider_error"


def test_public_adapter_has_no_execution_methods():
    source = BybitOrderbookDataSource(
        "BTCUSDT", transport=FakeTransport(BASE, NOW), clock=lambda: NOW
    )

    assert not hasattr(source, "place_order")
    assert not hasattr(source, "cancel_order")
    assert not hasattr(source, "execute_trade")


def test_constructor_rejects_bad_limits():
    with pytest.raises(ValueError):
        BybitOrderbookDataSource("BTCUSDT", category="option", limit=26)


def test_constructor_rejects_nonpositive_timeout():
    with pytest.raises(ValueError):
        BybitOrderbookDataSource("BTCUSDT", timeout_seconds=0)
