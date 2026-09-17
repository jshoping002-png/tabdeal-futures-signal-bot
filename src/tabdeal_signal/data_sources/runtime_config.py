"""Validated runtime configuration for unresolved public source endpoints.

The existing source reports deliberately leave some endpoint details unresolved.
This module provides a strict, non-secret runtime boundary for supplying those
URLs without adding guessed endpoints to source control.
"""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qsl, urlparse

from .source_access import VERIFIED_SOURCE_ACCESS_SPECS


_FORBIDDEN_AUTH_KEYS = {
    "api_key", "apikey", "api-key", "secret", "signature",
    "access_token", "auth_token", "authorization", "bearer",
}


def _host_is_within(hostname: str, allowed_hosts: tuple[str, ...]) -> bool:
    normalized = hostname.strip().lower()
    return any(normalized == host or normalized.endswith("." + host) for host in allowed_hosts)


def _validate_host_values(hosts: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(hosts, tuple) or not hosts or any(
        not isinstance(host, str) or not host.strip() for host in hosts
    ):
        raise ValueError("allowed_hosts must contain non-empty hosts")
    normalized = tuple(host.strip().lower() for host in hosts)
    if any(host.startswith(".") or "/" in host or "@" in host or host == "*" for host in normalized):
        raise ValueError("allowed_hosts must contain hostname values only")
    return normalized


@dataclass(frozen=True, slots=True)
class RuntimeEndpointConfig:
    source_id: str
    endpoint: str
    allowed_hosts: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise ValueError("source_id must be non-empty")
        if not isinstance(self.endpoint, str) or not self.endpoint.strip():
            raise ValueError("endpoint must be non-empty")
        allowed_hosts = _validate_host_values(self.allowed_hosts)
        parsed = urlparse(self.endpoint.strip())
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError("runtime source endpoint must be HTTPS")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("runtime endpoint must not contain URL userinfo")
        hostname = parsed.hostname.lower()
        if not _host_is_within(hostname, allowed_hosts):
            raise ValueError("runtime endpoint host is outside the configured source scope")
        if any(key.strip().lower() in _FORBIDDEN_AUTH_KEYS for key, _ in parse_qsl(parsed.query, keep_blank_values=True)):
            raise ValueError("runtime endpoint must not contain authentication material")
        object.__setattr__(self, "endpoint", self.endpoint.strip())
        object.__setattr__(self, "allowed_hosts", allowed_hosts)


KNOWN_RUNTIME_SOURCE_HOSTS: dict[str, tuple[str, ...]] = {
    spec.source_id: spec.verified_hosts
    for spec in VERIFIED_SOURCE_ACCESS_SPECS
    if spec.verified_hosts
}

RUNTIME_CONFIGURED_SOURCE_IDS: tuple[str, ...] = (
    "binance-spot-market-data",
    "us-treasury-daily-interest-rates",
    "sec-edgar-public-api",
    "okx-market-data",
    "coinbase-advanced-trade-market-data",
    "cftc-public-reporting",
    "coinmarketcap-keyless-public-api",
    "bis-statistics-api",
    "eurostat-rest-sdmx-api",
    "ny-fed-markets-data",
)


def runtime_endpoint_config(source_id: str, endpoint: str) -> RuntimeEndpointConfig:
    if source_id not in RUNTIME_CONFIGURED_SOURCE_IDS:
        raise KeyError(source_id)
    allowed_hosts = KNOWN_RUNTIME_SOURCE_HOSTS.get(source_id)
    if not allowed_hosts:
        raise ValueError("source requires an explicit runtime host allowlist")
    return RuntimeEndpointConfig(source_id, endpoint, allowed_hosts)


def explicit_runtime_endpoint_config(
    source_id: str, endpoint: str, allowed_hosts: tuple[str, ...]
) -> RuntimeEndpointConfig:
    if source_id not in RUNTIME_CONFIGURED_SOURCE_IDS:
        raise KeyError(source_id)
    normalized_allowed = _validate_host_values(allowed_hosts)
    known_hosts = KNOWN_RUNTIME_SOURCE_HOSTS.get(source_id)
    if known_hosts and any(not _host_is_within(host, known_hosts) for host in normalized_allowed):
        raise ValueError("explicit runtime host allowlist escapes the source's known host scope")
    return RuntimeEndpointConfig(source_id, endpoint, normalized_allowed)


__all__ = [
    "KNOWN_RUNTIME_SOURCE_HOSTS",
    "RUNTIME_CONFIGURED_SOURCE_IDS",
    "RuntimeEndpointConfig",
    "explicit_runtime_endpoint_config",
    "runtime_endpoint_config",
]
