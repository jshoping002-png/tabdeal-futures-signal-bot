from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from typing import Mapping
from urllib.error import HTTPError, URLError

from tabdeal_signal.data_sources.bybit import UrllibJsonTransport

_ENDPOINT = "/v5/market/kline"
_INTERVAL_MINUTES = {
    "1": 1, "3": 3, "5": 5, "15": 15, "30": 30,
    "60": 60, "120": 120, "240": 240, "360": 360, "720": 720,
}
_CATEGORIES = {"spot", "linear", "inverse"}


def _validate_candles(*, rows: list[object], timeframe: str, received_at: datetime) -> tuple[int, int]:
    interval_ms = _INTERVAL_MINUTES[timeframe] * 60 * 1000
    received_ms = int(received_at.timestamp() * 1000)
    closed_starts: list[int] = []
    for row in rows:
        if not isinstance(row, list) or len(row) < 7:
            raise ValueError("each Kline row must contain at least 7 fields")
        try:
            start_ms = int(row[0])
        except (TypeError, ValueError) as exc:
            raise ValueError("Kline startTime must be an integer timestamp") from exc
        if start_ms < 0:
            raise ValueError("Kline startTime must be non-negative")
        if start_ms + interval_ms <= received_ms:
            closed_starts.append(start_ms)
    if not closed_starts:
        raise ValueError("no closed Kline candle was available at received_at")
    return len(closed_starts), max(closed_starts)


def probe_kline(*, symbol: str, category: str, timeframe: str, limit: int,
                timeout_seconds: float, base_url: str = "https://api.bybit.com") -> dict[str, object]:
    symbol = symbol.strip().upper()
    category = category.strip().lower()
    timeframe = timeframe.strip()
    if not symbol:
        raise ValueError("symbol must not be empty")
    if category not in _CATEGORIES:
        raise ValueError("unsupported Bybit category")
    if timeframe not in _INTERVAL_MINUTES:
        raise ValueError("unsupported Bybit fixed-duration timeframe")
    if type(limit) is not int or not 1 <= limit <= 1000:
        raise ValueError("limit must be an integer in 1..1000")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")

    requested_at = datetime.now(timezone.utc)
    params = {
        "category": category,
        "symbol": symbol,
        "interval": timeframe,
        "end": str(int(requested_at.timestamp() * 1000)),
        "limit": str(limit),
    }
    started = time.monotonic()
    payload, received_at = UrllibJsonTransport(base_url).get(_ENDPOINT, params, timeout_seconds)
    received_at = received_at.astimezone(timezone.utc)
    elapsed_ms = round((time.monotonic() - started) * 1000, 2)
    if requested_at > received_at:
        raise ValueError("received_at precedes requested_at")

    ret_code = payload.get("retCode")
    if type(ret_code) is not int:
        raise ValueError("retCode must be an integer")
    if ret_code != 0:
        raise ValueError(f"Bybit provider error: {ret_code}")

    result = payload.get("result")
    if not isinstance(result, Mapping):
        raise ValueError("result must be an object")
    if result.get("symbol") != symbol:
        raise ValueError("response symbol mismatch")
    if result.get("category") != category:
        raise ValueError("response category mismatch")
    rows = result.get("list")
    if not isinstance(rows, list) or not rows:
        raise ValueError("result.list must be a non-empty list")

    closed_rows, latest_closed_start_ms = _validate_candles(
        rows=rows, timeframe=timeframe, received_at=received_at
    )
    latest_closed_start = datetime.fromtimestamp(latest_closed_start_ms / 1000, tz=timezone.utc)

    return {
        "ok": True,
        "endpoint": f"{base_url.rstrip('/')}{_ENDPOINT}",
        "symbol": symbol,
        "category": category,
        "timeframe": timeframe,
        "requested_at": requested_at.isoformat(),
        "received_at": received_at.isoformat(),
        "elapsed_ms": elapsed_ms,
        "ret_code": ret_code,
        "candle_rows": len(rows),
        "closed_candle_rows": closed_rows,
        "latest_closed_candle_start": latest_closed_start.isoformat(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only live connectivity probe for Bybit V5 public Kline API.")
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--category", default="linear", choices=sorted(_CATEGORIES))
    parser.add_argument("--timeframe", default="60", choices=sorted(_INTERVAL_MINUTES))
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--base-url", default="https://api.bybit.com")
    args = parser.parse_args(argv)
    try:
        result = probe_kline(symbol=args.symbol, category=args.category, timeframe=args.timeframe,
                             limit=args.limit, timeout_seconds=args.timeout, base_url=args.base_url)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error_type": type(exc).__name__, "error": str(exc)},
                         ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
