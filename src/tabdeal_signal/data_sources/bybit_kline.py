from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from math import isfinite

from tabdeal_signal.data.contracts import MarketDataSource, MarketSnapshot, SnapshotRequest
from tabdeal_signal.domain.contracts import Candle, UTC

from .bybit import JsonTransport, UrllibJsonTransport

_KLINE_ENDPOINT = "/v5/market/kline"
_INTERVAL_MINUTES = {
    "1": 1,
    "3": 3,
    "5": 5,
    "15": 15,
    "30": 30,
    "60": 60,
    "120": 120,
    "240": 240,
    "360": 360,
    "720": 720,
}
_CATEGORY_LIMITS = {"spot": (1, 1000), "linear": (1, 1000), "inverse": (1, 1000)}


def _candle_close(open_time: datetime, timeframe: str) -> datetime:
    return open_time + timedelta(minutes=_INTERVAL_MINUTES[timeframe])


class BybitKlineDataSource(MarketDataSource):
    """Read-only Bybit V5 Kline source for fixed-duration candle intervals."""

    _PROVENANCE = "bybit-v5-public-kline-docs@75994fda16e052aaad6e3fade82fd1f6fd90288e"

    def __init__(
        self,
        symbol: str,
        *,
        category: str = "linear",
        timeframe: str = "60",
        limit: int = 200,
        timeout_seconds: float = 5.0,
        transport: JsonTransport | None = None,
    ) -> None:
        self.symbol = symbol.strip().upper()
        self.category = category.strip().lower()
        self.timeframe = timeframe.strip()
        self.limit = limit
        self.timeout_seconds = timeout_seconds

        if not self.symbol:
            raise ValueError("symbol must not be empty")
        if self.category not in _CATEGORY_LIMITS:
            raise ValueError("unsupported Bybit category")
        if self.timeframe not in _INTERVAL_MINUTES:
            raise ValueError("timeframe must use a documented fixed-duration Bybit interval")
        low, high = _CATEGORY_LIMITS[self.category]
        if type(limit) is not int or not low <= limit <= high:
            raise ValueError("limit outside documented Bybit range")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

        self.source_id = f"bybit-v5-public-kline:{self.category}:{self.symbol}:{self.timeframe}"
        self._transport = transport or UrllibJsonTransport()

    def snapshot(self, request: SnapshotRequest) -> MarketSnapshot:
        if not isinstance(request, SnapshotRequest):
            raise ValueError("request must be a SnapshotRequest")
        if request.symbols != (self.symbol,) or request.timeframes != (self.timeframe,):
            raise ValueError("request scope must exactly match adapter")
        reference_time = request.reference_time
        if reference_time.tzinfo != UTC:
            raise ValueError("reference_time must be UTC")

        payload, received_at = self._transport.get(
            _KLINE_ENDPOINT,
            {
                "category": self.category,
                "symbol": self.symbol,
                "interval": self.timeframe,
                "end": str(int(reference_time.timestamp() * 1000)),
                "limit": str(self.limit),
            },
            self.timeout_seconds,
        )
        if received_at.tzinfo is None or received_at.utcoffset() is None:
            raise ValueError("transport received_at must be timezone-aware")
        received_at = received_at.astimezone(timezone.utc)
        if received_at > reference_time:
            raise ValueError("provider response was received after reference_time")

        ret_code = payload.get("retCode")
        if type(ret_code) is not int:
            raise ValueError("retCode must be an integer")
        if ret_code != 0:
            raise ValueError(f"Bybit provider error: {ret_code}")

        result = payload.get("result")
        if not isinstance(result, Mapping):
            raise ValueError("result must be an object")
        if result.get("symbol") != self.symbol:
            raise ValueError("response symbol mismatch")
        rows = result.get("list")
        if not isinstance(rows, list):
            raise ValueError("result.list must be a list")

        candles = [self._parse_candle(row) for row in rows]
        candles = [candle for candle in candles if candle.close_time < reference_time]
        if not candles:
            raise ValueError("no closed candle available at reference_time")

        candles.sort(key=lambda candle: candle.open_time)
        open_times = [candle.open_time for candle in candles]
        if len(open_times) != len(set(open_times)):
            raise ValueError("duplicate candles")
        for previous, current in zip(candles, candles[1:]):
            if current.open_time != previous.close_time:
                raise ValueError("gapped candle series")

        snapshot_id = f"{self.source_id}@{reference_time.isoformat()}"
        return MarketSnapshot(
            snapshot_id=snapshot_id,
            source_id=self.source_id,
            reference_time=reference_time,
            candles=tuple(candles),
        )

    def _parse_candle(self, row: object) -> Candle:
        if not isinstance(row, list) or len(row) != 7:
            raise ValueError("kline row must contain seven fields")
        if any(type(value) is not str for value in row):
            raise ValueError("kline fields must be strings")
        try:
            open_ms = int(row[0])
            values = [float(Decimal(row[index])) for index in range(1, 6)]
        except (InvalidOperation, ValueError) as exc:
            raise ValueError("invalid kline numeric value") from exc
        if not all(isfinite(value) for value in values):
            raise ValueError("kline numeric values must be finite")
        open_time = datetime.fromtimestamp(open_ms / 1000, UTC)
        close_time = _candle_close(open_time, self.timeframe)
        return Candle(
            symbol=self.symbol,
            timeframe=self.timeframe,
            open_time=open_time,
            close_time=close_time,
            open=values[0],
            high=values[1],
            low=values[2],
            close=values[3],
            volume=values[4],
        )


__all__ = ["BybitKlineDataSource"]
