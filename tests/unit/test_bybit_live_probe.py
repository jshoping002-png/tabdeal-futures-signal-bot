from datetime import datetime, timezone
import importlib.util
from pathlib import Path


_PROBE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "bybit_live_probe.py"
_SPEC = importlib.util.spec_from_file_location("bybit_live_probe", _PROBE_PATH)
assert _SPEC is not None and _SPEC.loader is not None
probe_module = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(probe_module)


class FakeTransport:
    def __init__(self, payload, received_at):
        self.payload = payload
        self.received_at = received_at

    def get(self, path, params, timeout_seconds):
        assert path == "/v5/market/kline"
        assert params["category"] == "linear"
        assert params["symbol"] == "BTCUSDT"
        assert params["interval"] == "60"
        assert params["limit"] == "5"
        assert timeout_seconds == 5
        return self.payload, self.received_at


def _payload(start_ms):
    return {
        "retCode": 0,
        "result": {
            "symbol": "BTCUSDT",
            "category": "linear",
            "list": [[str(start_ms), "2", "1", "1.5", "3", "4", "5"]],
        },
    }


def test_probe_validates_public_response_and_closed_candle(monkeypatch):
    received = datetime(2026, 1, 1, 2, 0, tzinfo=timezone.utc)
    start_ms = int(datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
    monkeypatch.setattr(
        probe_module,
        "UrllibJsonTransport",
        lambda base_url: FakeTransport(_payload(start_ms), received),
    )
    result = probe_module.probe_kline(
        symbol="btcusdt",
        category="linear",
        timeframe="60",
        limit=5,
        timeout_seconds=5,
    )
    assert result["ok"] is True
    assert result["ret_code"] == 0
    assert result["candle_rows"] == 1
    assert result["closed_candle_rows"] == 1
    assert result["latest_closed_candle_start"] == "2026-01-01T00:00:00+00:00"


def test_probe_rejects_provider_error(monkeypatch):
    payload = {"retCode": 10006, "retMsg": "rate limit"}
    monkeypatch.setattr(
        probe_module,
        "UrllibJsonTransport",
        lambda base_url: FakeTransport(payload, datetime.now(timezone.utc)),
    )
    try:
        probe_module.probe_kline(
            symbol="BTCUSDT",
            category="linear",
            timeframe="60",
            limit=5,
            timeout_seconds=5,
        )
    except ValueError as exc:
        assert "Bybit provider error" in str(exc)
    else:
        raise AssertionError("provider error was not rejected")


def test_probe_rejects_when_all_returned_candles_are_open(monkeypatch):
    received = datetime(2026, 1, 1, 0, 30, tzinfo=timezone.utc)
    start_ms = int(datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
    monkeypatch.setattr(
        probe_module,
        "UrllibJsonTransport",
        lambda base_url: FakeTransport(_payload(start_ms), received),
    )
    try:
        probe_module.probe_kline(
            symbol="BTCUSDT",
            category="linear",
            timeframe="60",
            limit=5,
            timeout_seconds=5,
        )
    except ValueError as exc:
        assert "no closed Kline candle" in str(exc)
    else:
        raise AssertionError("open candle was accepted")
