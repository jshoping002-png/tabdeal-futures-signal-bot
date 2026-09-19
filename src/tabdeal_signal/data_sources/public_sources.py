"""Public, read-only HTTP access layer for previously verified sources.

The source-verification batches establish public access boundaries but leave
some exact dataset paths, series identifiers, and provider-specific schemas
unresolved. This module therefore requires the exact runtime endpoint from the
caller and stops at a safe source envelope; it never invents a dataset or a
strategy meaning.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from json import JSONDecodeError, dumps, loads
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener
import xml.etree.ElementTree as ET

from .contracts import (
    DataProvenance,
    DataQualityStatus,
    DataSnapshotMetadata,
    NormalizedSnapshot,
    ReadOnlyDataSource,
    SourceKind,
)


@dataclass(frozen=True, slots=True)
class PublicHttpResponse:
    status_code: int
    received_at: datetime
    body: bytes
    content_type: str = ""

    def __post_init__(self) -> None:
        if type(self.status_code) is not int or not 100 <= self.status_code <= 599:
            raise ValueError("status_code must be an HTTP integer status")
        if not isinstance(self.received_at, datetime):
            raise ValueError("received_at must be a datetime")
        if self.received_at.tzinfo is None or self.received_at.utcoffset() is None:
            raise ValueError("received_at must be timezone-aware")
        if not isinstance(self.body, bytes):
            raise ValueError("body must be bytes")
        if not isinstance(self.content_type, str):
            raise ValueError("content_type must be a string")
        object.__setattr__(self, "received_at", self.received_at.astimezone(timezone.utc))


class PublicHttpTransport(Protocol):
    def request(
        self,
        method: str,
        url: str,
        *,
        query: Mapping[str, str] | None,
        body: bytes | None,
        content_type: str | None,
        timeout_seconds: float,
    ) -> PublicHttpResponse:
        ...


class _NoRedirectHandler(HTTPRedirectHandler):
    """Reject redirects so the initial host allowlist remains authoritative."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class UrllibPublicHttpTransport:
    """GET/POST-only transport with no credential or authentication surface."""

    def __init__(self, *, user_agent: str = "tabdeal-read-only-data-source/1") -> None:
        if not isinstance(user_agent, str) or not user_agent.strip():
            raise ValueError("user_agent must be a non-empty string")
        self._user_agent = user_agent.strip()

    def request(
        self,
        method: str,
        url: str,
        *,
        query: Mapping[str, str] | None,
        body: bytes | None,
        content_type: str | None,
        timeout_seconds: float,
    ) -> PublicHttpResponse:
        if not isinstance(method, str):
            raise ValueError("method must be a string")
        method = method.strip().upper()
        if method not in {"GET", "POST"}:
            raise ValueError("only GET and POST are allowed by the public read-only transport")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError("public source endpoint must use HTTPS")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("public source endpoint must not contain URL userinfo")
        for key, _ in parse_qsl(parsed.query, keep_blank_values=True):
            if key.strip().lower() in _FORBIDDEN_AUTH_KEYS:
                raise ValueError("public source endpoint must not contain authentication material")
        if query is not None:
            _reject_auth_keys(query, field="query")
        if body is not None and method == "GET":
            raise ValueError("GET requests cannot carry a body")
        final_url = url
        if query:
            final_url = f"{url}{'&' if '?' in url else '?'}{urlencode(query)}"
        headers = {
            "Accept": "application/json, application/xml, text/xml, text/plain;q=0.9, */*;q=0.1",
            "User-Agent": self._user_agent,
        }
        if body is not None:
            headers["Content-Type"] = content_type or "application/json"
        request = Request(final_url, data=body, headers=headers, method=method)
        try:
            with build_opener(_NoRedirectHandler()).open(request, timeout=timeout_seconds) as response:
                received_at = datetime.now(timezone.utc)
                response_body = response.read()
                response_type = response.headers.get("Content-Type", "")
                return PublicHttpResponse(response.status, received_at, response_body, response_type)
        except HTTPError as exc:
            received_at = datetime.now(timezone.utc)
            response_body = exc.read()
            response_type = exc.headers.get("Content-Type", "") if exc.headers else ""
            return PublicHttpResponse(exc.code, received_at, response_body, response_type)
        except (TimeoutError, URLError, OSError) as exc:
            raise PublicTransportError(type(exc).__name__, str(exc)) from exc


class PublicTransportError(RuntimeError):
    """Transport failure without exposing or carrying credentials."""

    def __init__(self, error_class: str, detail: str) -> None:
        super().__init__(detail)
        self.error_class = error_class
        self.detail = detail


_FORBIDDEN_AUTH_KEYS = {
    "api_key", "apikey", "api-key", "secret", "signature",
    "access_token", "auth_token", "authorization", "bearer",
}


def _reject_auth_keys(mapping: Mapping[str, object], *, field: str) -> None:
    for key, value in mapping.items():
        if not isinstance(key, str):
            raise ValueError(f"{field} keys must be strings")
        normalized = key.strip().lower()
        if normalized in _FORBIDDEN_AUTH_KEYS:
            raise ValueError(f"{field} must not contain authentication material")
        if isinstance(value, Mapping):
            _reject_auth_keys(value, field=field)
        elif isinstance(value, (list, tuple)):
            for item in value:
                if isinstance(item, Mapping):
                    _reject_auth_keys(item, field=field)


class _ConfiguredPublicSource(ReadOnlyDataSource):
    _ALLOWED_METHODS = {"GET", "POST"}

    def __init__(
        self,
        *,
        source_id: str,
        source_kind: SourceKind,
        endpoint: str,
        topic: str,
        schema_version: str,
        allowed_hosts: tuple[str, ...],
        method: str = "GET",
        query: Mapping[str, str] | None = None,
        body: Mapping[str, object] | None = None,
        timeout_seconds: float = 10.0,
        transport: PublicHttpTransport | None = None,
    ) -> None:
        for name, value in (
            ("source_id", source_id),
            ("endpoint", endpoint),
            ("topic", topic),
            ("schema_version", schema_version),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(allowed_hosts, tuple) or not allowed_hosts or any(
            not isinstance(host, str) or not host.strip() for host in allowed_hosts
        ):
            raise ValueError("allowed_hosts must contain one or more non-empty host strings")
        parsed = urlparse(endpoint)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError("endpoint must be an HTTPS URL")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("endpoint must not contain URL userinfo")
        hostname = parsed.hostname.lower()
        allowed = tuple(host.lower().strip() for host in allowed_hosts)
        if hostname not in allowed and not any(hostname.endswith("." + host) for host in allowed):
            raise ValueError("endpoint host is not allowed for this source")
        if not isinstance(method, str):
            raise ValueError("method must be a string")
        method = method.strip().upper()
        if method not in self._ALLOWED_METHODS:
            raise ValueError("only GET and POST are supported")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if method == "GET" and body is not None:
            raise ValueError("GET source cannot define a request body")
        if query is not None:
            _reject_auth_keys(query, field="query")
        if body is not None:
            _reject_auth_keys(body, field="body")
        self.source_id = source_id.strip()
        self.source_kind = source_kind
        self.endpoint = endpoint
        self.topic = topic.strip()
        self.schema_version = schema_version.strip()
        self.method = method
        self.query = dict(query or {})
        self.body = dict(body) if body is not None else None
        self.timeout_seconds = timeout_seconds
        self._transport = transport or UrllibPublicHttpTransport()
        self._provenance = DataProvenance(self.source_id, endpoint, self.schema_version)

    def fetch_snapshot(self, *, as_of: datetime | None = None) -> NormalizedSnapshot:
        if as_of is not None:
            if as_of.tzinfo is None or as_of.utcoffset() is None:
                raise ValueError("as_of must be timezone-aware")
            as_of = as_of.astimezone(timezone.utc)
        body = None if self.body is None else dumps(self.body, separators=(",", ":"), sort_keys=True).encode("utf-8")
        try:
            response = self._transport.request(
                self.method,
                self.endpoint,
                query=self.query,
                body=body,
                content_type="application/json" if body is not None else None,
                timeout_seconds=self.timeout_seconds,
            )
        except PublicTransportError as exc:
            return self._failure(self._now(), "transport_error", exc.error_class, exc.detail)
        if not isinstance(response, PublicHttpResponse):
            return self._failure(self._now(), "transport_error", "invalid_response_type")
        received_at = response.received_at
        # HTTP failures describe provider/transport state, not usable data.
        # Classify them before PIT checks so a historical as_of cannot hide
        # the documented rate-limit or HTTP error class.
        if response.status_code == 429:
            return self._failure(received_at, "rate_limited", "http_429")
        if response.status_code < 200 or response.status_code >= 300:
            return self._failure(received_at, "http_error", str(response.status_code))
        if as_of is not None and received_at > as_of:
            return self._failure(received_at, "pit_unavailable", "received_after_as_of")
        return self._decode(response, received_at)

    def _decode(self, response: PublicHttpResponse, received_at: datetime) -> NormalizedSnapshot:
        raise NotImplementedError

    def _success(self, received_at: datetime, values: Mapping[str, object]) -> NormalizedSnapshot:
        return NormalizedSnapshot(
            metadata=DataSnapshotMetadata(
                source_kind=self.source_kind,
                instrument_or_topic=self.topic,
                received_at=received_at,
                available_at=received_at,
                quality=DataQualityStatus.VALID,
                provenance=self._provenance,
            ),
            values=values,
        )

    def _failure(self, received_at: datetime, error_class: str, *detail: str) -> NormalizedSnapshot:
        quality = (
            DataQualityStatus.INVALID
            if error_class in {"invalid_json", "invalid_xml", "invalid_text", "schema_error"}
            else DataQualityStatus.UNAVAILABLE
        )
        return NormalizedSnapshot(
            metadata=DataSnapshotMetadata(
                source_kind=self.source_kind,
                instrument_or_topic=self.topic,
                received_at=received_at,
                available_at=received_at,
                quality=quality,
                provenance=self._provenance,
            ),
            values={
                "source_id": self.source_id,
                "error_class": error_class,
                "error_detail": "|".join(detail),
            },
        )

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)


class OfficialPublicJsonDataSource(_ConfiguredPublicSource):
    """JSON envelope for a verified public JSON API endpoint."""

    def _decode(self, response: PublicHttpResponse, received_at: datetime) -> NormalizedSnapshot:
        try:
            payload = loads(response.body.decode("utf-8"))
        except (UnicodeDecodeError, JSONDecodeError):
            return self._failure(received_at, "invalid_json", "json_decode_error")
        return self._success(received_at, {"payload": payload, "content_type": response.content_type})


class OfficialPublicXmlDataSource(_ConfiguredPublicSource):
    """XML envelope for a verified public XML feed."""

    def _decode(self, response: PublicHttpResponse, received_at: datetime) -> NormalizedSnapshot:
        try:
            root = ET.fromstring(response.body)
            xml_text = response.body.decode("utf-8")
        except (ET.ParseError, UnicodeDecodeError, ValueError):
            return self._failure(received_at, "invalid_xml", "xml_parse_error")
        return self._success(
            received_at,
            {"root_tag": root.tag, "xml_text": xml_text, "content_type": response.content_type},
        )


class OfficialPublicTextDataSource(_ConfiguredPublicSource):
    """Raw UTF-8 text envelope for CSV/TSV/SDMX/RSS/RDF or other text feeds."""

    def _decode(self, response: PublicHttpResponse, received_at: datetime) -> NormalizedSnapshot:
        try:
            text = response.body.decode("utf-8")
        except UnicodeDecodeError:
            return self._failure(received_at, "invalid_text", "utf8_decode_error")
        return self._success(received_at, {"text": text, "content_type": response.content_type})


class BlsPublicApiDataSource(OfficialPublicJsonDataSource):
    """BLS public API access; exact endpoint/request shape is runtime-configured."""

    def __init__(self, *, endpoint: str, topic: str, schema_version: str, query: Mapping[str, str] | None = None, body: Mapping[str, object] | None = None, method: str = "POST", timeout_seconds: float = 10.0, transport: PublicHttpTransport | None = None) -> None:
        super().__init__(source_id="bls-public-api", source_kind=SourceKind.MACRO, endpoint=endpoint, topic=topic, schema_version=schema_version, allowed_hosts=("bls.gov",), method=method, query=query, body=body, timeout_seconds=timeout_seconds, transport=transport)


class TreasuryDailyRatesDataSource(OfficialPublicXmlDataSource):
    """Treasury Daily Interest Rate XML access with runtime-configured feed/params."""

    def __init__(self, *, endpoint: str, topic: str, schema_version: str, query: Mapping[str, str] | None = None, timeout_seconds: float = 10.0, transport: PublicHttpTransport | None = None) -> None:
        super().__init__(source_id="us-treasury-daily-interest-rates", source_kind=SourceKind.MACRO, endpoint=endpoint, topic=topic, schema_version=schema_version, allowed_hosts=("treasury.gov",), method="GET", query=query, timeout_seconds=timeout_seconds, transport=transport)


class SecEdgarDataSource(OfficialPublicJsonDataSource):
    """SEC EDGAR public JSON access; exact dataset endpoint is runtime-configured."""

    def __init__(self, *, endpoint: str, topic: str, schema_version: str, query: Mapping[str, str] | None = None, timeout_seconds: float = 10.0, transport: PublicHttpTransport | None = None) -> None:
        super().__init__(source_id="sec-edgar-public-api", source_kind=SourceKind.MACRO, endpoint=endpoint, topic=topic, schema_version=schema_version, allowed_hosts=("data.sec.gov",), method="GET", query=query, timeout_seconds=timeout_seconds, transport=transport)


class CftcPublicReportingDataSource(OfficialPublicTextDataSource):
    """CFTC Public Reporting Environment; preserves the published feed format."""

    def __init__(self, *, endpoint: str, topic: str, schema_version: str, query: Mapping[str, str] | None = None, timeout_seconds: float = 10.0, transport: PublicHttpTransport | None = None) -> None:
        super().__init__(source_id="cftc-public-reporting", source_kind=SourceKind.MACRO, endpoint=endpoint, topic=topic, schema_version=schema_version, allowed_hosts=("publicreporting.cftc.gov",), method="GET", query=query, timeout_seconds=timeout_seconds, transport=transport)


class CoinMarketCapKeylessDataSource(OfficialPublicJsonDataSource):
    """CoinMarketCap keyless public API access; exact endpoint is runtime-configured."""

    def __init__(self, *, endpoint: str, topic: str, schema_version: str, query: Mapping[str, str] | None = None, timeout_seconds: float = 10.0, transport: PublicHttpTransport | None = None) -> None:
        super().__init__(source_id="coinmarketcap-keyless-public-api", source_kind=SourceKind.AGGREGATOR, endpoint=endpoint, topic=topic, schema_version=schema_version, allowed_hosts=("pro-api.coinmarketcap.com",), method="GET", query=query, timeout_seconds=timeout_seconds, transport=transport)


class EcbSdmxDataSource(OfficialPublicTextDataSource):
    """ECB public SDMX access; preserves JSON/CSV/SDMX/XML text formats."""

    def __init__(self, *, endpoint: str, topic: str, schema_version: str, query: Mapping[str, str] | None = None, timeout_seconds: float = 10.0, transport: PublicHttpTransport | None = None) -> None:
        super().__init__(source_id="ecb-data-portal-api", source_kind=SourceKind.MACRO, endpoint=endpoint, topic=topic, schema_version=schema_version, allowed_hosts=("data-api.ecb.europa.eu",), method="GET", query=query, timeout_seconds=timeout_seconds, transport=transport)


class BisStatisticsDataSource(OfficialPublicTextDataSource):
    """BIS Statistics public API access with response format preserved."""

    def __init__(self, *, endpoint: str, topic: str, schema_version: str, query: Mapping[str, str] | None = None, timeout_seconds: float = 10.0, transport: PublicHttpTransport | None = None) -> None:
        super().__init__(source_id="bis-statistics-api", source_kind=SourceKind.MACRO, endpoint=endpoint, topic=topic, schema_version=schema_version, allowed_hosts=("stats.bis.org",), method="GET", query=query, timeout_seconds=timeout_seconds, transport=transport)


class EurostatDataSource(OfficialPublicTextDataSource):
    """Eurostat public REST/SDMX access with response format preserved."""

    def __init__(self, *, endpoint: str, topic: str, schema_version: str, query: Mapping[str, str] | None = None, timeout_seconds: float = 10.0, transport: PublicHttpTransport | None = None) -> None:
        super().__init__(source_id="eurostat-rest-sdmx-api", source_kind=SourceKind.MACRO, endpoint=endpoint, topic=topic, schema_version=schema_version, allowed_hosts=("ec.europa.eu",), method="GET", query=query, timeout_seconds=timeout_seconds, transport=transport)


__all__ = [
    "BlsPublicApiDataSource",
    "CftcPublicReportingDataSource",
    "CoinMarketCapKeylessDataSource",
    "EcbSdmxDataSource",
    "BisStatisticsDataSource",
    "EurostatDataSource",
    "OfficialPublicJsonDataSource",
    "OfficialPublicTextDataSource",
    "OfficialPublicXmlDataSource",
    "PublicHttpResponse",
    "PublicHttpTransport",
    "PublicTransportError",
    "SecEdgarDataSource",
    "TreasuryDailyRatesDataSource",
    "UrllibPublicHttpTransport",
]
