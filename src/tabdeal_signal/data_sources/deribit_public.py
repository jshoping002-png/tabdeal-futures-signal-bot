"""Read-only Deribit public JSON-RPC market-data adapter."""
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from json import dumps, loads
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .contracts import DataProvenance, DataQualityStatus, DataSnapshotMetadata, NormalizedSnapshot, ReadOnlyDataSource, SourceKind

_ALLOWED_METHODS = {
    "public/get_instruments",
    "public/ticker",
    "public/get_order_book",
    "public/get_tradingview_chart_data",
}
_CHART_METHOD = "public/get_tradingview_chart_data"
_CHART_RESOLUTIONS_MINUTES = {1, 3, 5, 10, 15, 30, 60, 120, 180, 360, 720}


class DeribitPublicMarketDataSource(ReadOnlyDataSource):
    """Call one documented public Deribit JSON-RPC method, preserving raw result."""

    _PROVENANCE = DataProvenance(
        source="deribit-public-market-data",
        reference="https://docs.deribit.com/",
        schema_version="deribit-report-003-public-market-data",
    )

    def __init__(
        self,
        method: str,
        *,
        params: Mapping[str, object] | None = None,
        request_id: int = 1,
        timeout_seconds: float = 5.0,
        transport=None,
        base_url: str = "https://www.deribit.com/api/v2",
    ) -> None:
        method = method.strip()
        if method not in _ALLOWED_METHODS:
            raise ValueError("method is outside the report-003 public Deribit allowlist")
        if type(request_id) is not int or request_id < 1:
            raise ValueError("request_id must be a positive integer")
        if params is not None and not isinstance(params, Mapping):
            raise ValueError("params must be a mapping")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if not isinstance(base_url, str) or not base_url.startswith("https://"):
            raise ValueError("base_url must be HTTPS")
        self.method = method
        self.params = dict(params or {})
        self.request_id = request_id
        self.timeout_seconds = timeout_seconds
        self.base_url = base_url.rstrip("/")
        self._transport = transport or _UrllibRpcTransport()

    def fetch_snapshot(self, *, as_of: datetime | None = None) -> NormalizedSnapshot:
        if as_of is not None:
            if as_of.tzinfo is None or as_of.utcoffset() is None:
                raise ValueError("as_of must be timezone-aware")
            as_of = as_of.astimezone(timezone.utc)
        topic = f"deribit-rpc:{self.method}"
        try:
            response, received_at = self._transport.post(
                f"{self.base_url}/", self.method, self.params, self.request_id, self.timeout_seconds
            )
            if received_at.tzinfo is None or received_at.utcoffset() is None:
                raise ValueError("transport received_at must be timezone-aware")
            received_at = received_at.astimezone(timezone.utc)
        except HTTPError as exc:
            return self._failure(topic, datetime.now(timezone.utc), "rate_limited" if exc.code in (403, 429) else "http_error", str(exc.code))
        except (TimeoutError, URLError, OSError) as exc:
            return self._failure(topic, datetime.now(timezone.utc), "transport_error", type(exc).__name__)
        except ValueError as exc:
            return self._failure(topic, datetime.now(timezone.utc), "invalid_payload", str(exc))
        if not isinstance(response, Mapping):
            return self._failure(topic, received_at, "schema_error", "expected_json_object")
        # Preserve documented provider errors before PIT gating so an
        # historical as_of cannot mask a provider-side failure.
        rpc_error = response.get("error")
        if rpc_error is not None:
            return self._failure(topic, received_at, "provider_error", str(rpc_error))
        if as_of is not None and received_at > as_of:
            return self._failure(topic, received_at, "pit_unavailable", "received_after_as_of")
        if "result" not in response:
            return self._failure(topic, received_at, "schema_error", "missing_result")
        result = response["result"]
        if self.method == _CHART_METHOD and as_of is not None:
            result, error = _pit_filter_chart_result(result, self.params, as_of)
            if error is not None:
                return self._failure(topic, received_at, "pit_unavailable", error)
        return NormalizedSnapshot(
            DataSnapshotMetadata(SourceKind.EXCHANGE, topic, received_at, available_at=received_at, quality=DataQualityStatus.VALID, provenance=self._PROVENANCE),
            {"method": self.method, "request_id": self.request_id, "params": dict(self.params), "result": result},
        )

    def _failure(self, topic: str, received_at: datetime, error_class: str, *detail: str) -> NormalizedSnapshot:
        quality = DataQualityStatus.INVALID if error_class in {"invalid_payload", "schema_error"} else DataQualityStatus.UNAVAILABLE
        return NormalizedSnapshot(DataSnapshotMetadata(SourceKind.EXCHANGE, topic, received_at, available_at=received_at, quality=quality, provenance=self._PROVENANCE), {"method": self.method, "error_class": error_class, "error_detail": "|".join(detail)})


def _pit_filter_chart_result(result, params: Mapping[str, object], as_of: datetime):
    """Retain only completed minute-resolution candles strictly before ``as_of``.

    Deribit's documented ``ticks`` are the candle time axis; the documented
    resolution is in full minutes. Daily bars are deliberately fail-closed
    because their calendar-close semantics are not specified here.
    """
    if not isinstance(result, Mapping):
        return None, "chart_result_not_object"
    if result.get("status") == "no_data":
        return result, None
    ticks = result.get("ticks")
    if not isinstance(ticks, list):
        return None, "chart_ticks_missing_or_invalid"
    resolution = params.get("resolution")
    try:
        resolution_minutes = int(resolution)
    except (TypeError, ValueError):
        resolution_minutes = None
    if resolution_minutes not in _CHART_RESOLUTIONS_MINUTES or str(resolution) == "1D":
        return None, "unsupported_chart_resolution_for_pit"
    close_cutoff_ms = int(as_of.timestamp() * 1000)
    completed_indices = []
    for index, tick in enumerate(ticks):
        if type(tick) is not int or tick < 0:
            return None, "invalid_chart_tick"
        close_at_ms = tick + resolution_minutes * 60_000
        if close_at_ms < close_cutoff_ms:
            completed_indices.append(index)
    if not completed_indices:
        return None, "no_completed_candle_before_as_of"
    filtered = dict(result)
    for key in ("ticks", "open", "high", "low", "close", "volume", "cost"):
        values = result.get(key)
        if values is None:
            continue
        if not isinstance(values, list) or len(values) != len(ticks):
            return None, f"chart_{key}_length_mismatch"
        filtered[key] = [values[index] for index in completed_indices]
    return filtered, None


class _UrllibRpcTransport:
    def post(self, url, method, params, request_id, timeout_seconds):
        body = dumps({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}, separators=(",", ":"), sort_keys=True).encode("utf-8")
        request = Request(url, data=body, headers={"Accept": "application/json", "Content-Type": "application/json"}, method="POST")
        with urlopen(request, timeout=timeout_seconds) as response:
            return loads(response.read().decode("utf-8")), datetime.now(timezone.utc)


__all__ = ["DeribitPublicMarketDataSource"]
