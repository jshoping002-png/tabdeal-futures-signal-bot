from datetime import datetime, timezone
from urllib.error import HTTPError

from tabdeal_signal.data_sources.bybit_funding import BybitFundingRateDataSource
from tabdeal_signal.data_sources.bybit_open_interest import BybitOpenInterestDataSource
from tabdeal_signal.data_sources.contracts import DataQualityStatus

UTC = timezone.utc


class FakeTransport:
    def __init__(self, payload, received_at):
        self.payload = payload
        self.received_at = received_at
        self.calls = []

    def get(self, path, params, timeout_seconds):
        self.calls.append((path, dict(params), timeout_seconds))
        return self.payload, self.received_at


def test_open_interest_normalizes_public_page_and_pit():
    received = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    transport = FakeTransport(
        {
            "retCode": 0,
            "result": {
                "list": [{
                    "symbol": "BTCUSDT",
                    "openInterest": "123.4500",
                    "singleOpenInterest": "123.4500",
                    "timestamp": "1767225600000",
                }],
                "nextPageCursor": "cursor-1",
            },
        },
        received,
    )
    source = BybitOpenInterestDataSource("btcusdt", transport=transport)
    snapshot = source.fetch_snapshot(as_of=received)
    assert snapshot.metadata.quality is DataQualityStatus.VALID
    assert snapshot.values["rows"][0]["open_interest"] == "123.4500"
    assert snapshot.values["next_page_cursor"] == "cursor-1"
    assert transport.calls[0][0] == "/v5/market/open-interest"
    assert transport.calls[0][1]["intervalTime"] == "5min"


def test_open_interest_rejects_future_observation_for_pit():
    received = datetime(2026, 1, 1, tzinfo=UTC)
    future_ms = int(datetime(2026, 1, 2, tzinfo=UTC).timestamp() * 1000)
    transport = FakeTransport(
        {
            "retCode": 0,
            "result": {
                "list": [{"symbol": "BTCUSDT", "openInterest": "1", "timestamp": str(future_ms)}]
            },
        },
        received,
    )
    snapshot = BybitOpenInterestDataSource("BTCUSDT", transport=transport).fetch_snapshot(as_of=received)
    assert snapshot.metadata.quality is DataQualityStatus.UNAVAILABLE
    assert snapshot.values["error_class"] == "pit_unavailable"


def test_open_interest_classifies_http_rate_limits_without_raising():
    class RateLimitedTransport:
        def get(self, *args, **kwargs):
            raise HTTPError(
                "https://api.bybit.com/v5/market/open-interest",
                429,
                "Too Many Requests",
                {},
                None,
            )

    snapshot = BybitOpenInterestDataSource(
        "BTCUSDT", transport=RateLimitedTransport()
    ).fetch_snapshot()

    assert snapshot.metadata.quality is DataQualityStatus.UNAVAILABLE
    assert snapshot.values["error_class"] == "rate_limited"
    assert snapshot.values["error_detail"] == "429"


def test_open_interest_and_funding_classify_provider_rate_limits():
    received = datetime(2026, 1, 1, tzinfo=UTC)
    transport = FakeTransport({"retCode": 10006, "result": {}}, received)

    open_interest = BybitOpenInterestDataSource(
        "BTCUSDT", transport=transport
    ).fetch_snapshot()
    funding = BybitFundingRateDataSource(
        "BTCUSDT", transport=transport
    ).fetch_snapshot()

    for snapshot in (open_interest, funding):
        assert snapshot.metadata.quality is DataQualityStatus.UNAVAILABLE
        assert snapshot.values["error_class"] == "rate_limited"
        assert snapshot.values["error_detail"] == "10006"


def test_funding_history_normalizes_rate_and_timestamp():
    received = datetime(2026, 1, 1, tzinfo=UTC)
    transport = FakeTransport(
        {
            "retCode": 0,
            "result": {
                "list": [{
                    "symbol": "BTCUSDT",
                    "fundingRate": "0.000100",
                    "fundingRateTimestamp": "1767225600000",
                }]
            },
        },
        received,
    )
    source = BybitFundingRateDataSource("BTCUSDT", transport=transport)
    snapshot = source.fetch_snapshot(as_of=received)
    assert snapshot.metadata.quality is DataQualityStatus.VALID
    row = snapshot.values["rows"][0]
    assert row["funding_rate"] == "0.000100"
    assert row["funding_rate_timestamp_ms"] == 1767225600000
    assert transport.calls[0][0] == "/v5/market/funding/history"


def test_funding_history_requires_end_time_when_start_time_is_used():
    start = datetime(2025, 12, 1, tzinfo=UTC)
    try:
        BybitFundingRateDataSource("BTCUSDT", start_time=start)
    except ValueError:
        pass
    else:
        raise AssertionError("start_time without end_time must be rejected")


def test_funding_history_enforces_documented_limit_and_category():
    try:
        BybitFundingRateDataSource("BTCUSDT", limit=201)
    except ValueError:
        pass
    else:
        raise AssertionError("limit > 200 must be rejected")
    try:
        BybitOpenInterestDataSource("BTCUSDT", category="spot")
    except ValueError:
        pass
    else:
        raise AssertionError("spot Open Interest must be rejected")


def test_both_adapters_are_read_only():
    assert not hasattr(BybitOpenInterestDataSource, "place_order")
    assert not hasattr(BybitFundingRateDataSource, "place_order")


def test_bybit_redirect_handler_rejects_redirects():
    from tabdeal_signal.data_sources.bybit import _NoRedirectHandler

    assert _NoRedirectHandler().redirect_request(None, None, 302, "Found", {}, "https://attacker.example/") is None
