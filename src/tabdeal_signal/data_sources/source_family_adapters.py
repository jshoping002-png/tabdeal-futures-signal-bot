"""Read-only adapters for source families whose exact endpoint remains runtime-configured.

These adapters turn the verified public-access boundaries into concrete source
objects without inventing dataset paths, series identifiers, or strategy meaning.
"""
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

from .contracts import NormalizedSnapshot, SourceKind
from .public_sources import (
    OfficialPublicJsonDataSource,
    OfficialPublicTextDataSource,
    PublicHttpResponse,
    PublicHttpTransport,
    _ConfiguredPublicSource,
)


class BinanceSpotMarketDataSource(OfficialPublicJsonDataSource):
    """Binance Spot public market-data boundary; exact endpoint is runtime-configured."""

    def __init__(
        self,
        *,
        endpoint: str,
        topic: str,
        schema_version: str,
        query: Mapping[str, str] | None = None,
        timeout_seconds: float = 10.0,
        transport: PublicHttpTransport | None = None,
    ) -> None:
        super().__init__(
            source_id="binance-spot-market-data",
            source_kind=SourceKind.EXCHANGE,
            endpoint=endpoint,
            topic=topic,
            schema_version=schema_version,
            allowed_hosts=("data-api.binance.vision",),
            method="GET",
            query=query,
            timeout_seconds=timeout_seconds,
            transport=transport,
        )


class OkxMarketDataSource(OfficialPublicJsonDataSource):
    """OKX public market-data boundary with region-aware runtime endpoints."""

    def __init__(
        self,
        *,
        endpoint: str,
        topic: str,
        schema_version: str,
        query: Mapping[str, str] | None = None,
        timeout_seconds: float = 10.0,
        transport: PublicHttpTransport | None = None,
    ) -> None:
        super().__init__(
            source_id="okx-market-data",
            source_kind=SourceKind.EXCHANGE,
            endpoint=endpoint,
            topic=topic,
            schema_version=schema_version,
            allowed_hosts=("okx.com",),
            method="GET",
            query=query,
            timeout_seconds=timeout_seconds,
            transport=transport,
        )


class CoinbaseAdvancedTradeMarketDataSource(_ConfiguredPublicSource):
    """Coinbase Advanced Trade public market-data envelope.

    The source reports verify the public REST/WebSocket boundary but do not
    establish a single project endpoint host. The caller must therefore supply
    the explicitly approved HTTPS host rather than having this adapter guess it.
    """

    def __init__(
        self,
        *,
        endpoint: str,
        topic: str,
        schema_version: str,
        allowed_hosts: tuple[str, ...],
        query: Mapping[str, str] | None = None,
        timeout_seconds: float = 10.0,
        transport: PublicHttpTransport | None = None,
    ) -> None:
        super().__init__(
            source_id="coinbase-advanced-trade-market-data",
            source_kind=SourceKind.EXCHANGE,
            endpoint=endpoint,
            topic=topic,
            schema_version=schema_version,
            allowed_hosts=allowed_hosts,
            method="GET",
            query=query,
            timeout_seconds=timeout_seconds,
            transport=transport,
        )

    def _decode(
        self, response: PublicHttpResponse, received_at: datetime
    ) -> NormalizedSnapshot:
        return OfficialPublicJsonDataSource._decode(self, response, received_at)


class OecdSdmxDataSource(OfficialPublicTextDataSource):
    """OECD Data Explorer public SDMX boundary; exact dataset is runtime-configured."""

    def __init__(
        self,
        *,
        endpoint: str,
        topic: str,
        schema_version: str,
        query: Mapping[str, str] | None = None,
        timeout_seconds: float = 10.0,
        transport: PublicHttpTransport | None = None,
    ) -> None:
        super().__init__(
            source_id="oecd-data-explorer-sdmx",
            source_kind=SourceKind.MACRO,
            endpoint=endpoint,
            topic=topic,
            schema_version=schema_version,
            allowed_hosts=("sdmx.oecd.org",),
            method="GET",
            query=query,
            timeout_seconds=timeout_seconds,
            transport=transport,
        )


class NyFedMarketsDataSource(OfficialPublicTextDataSource):
    """New York Fed Markets Data public API family; route is runtime-configured."""

    def __init__(
        self,
        *,
        endpoint: str,
        topic: str,
        schema_version: str,
        query: Mapping[str, str] | None = None,
        timeout_seconds: float = 10.0,
        transport: PublicHttpTransport | None = None,
    ) -> None:
        super().__init__(
            source_id="ny-fed-markets-data",
            source_kind=SourceKind.MACRO,
            endpoint=endpoint,
            topic=topic,
            schema_version=schema_version,
            allowed_hosts=("markets.newyorkfed.org",),
            method="GET",
            query=query,
            timeout_seconds=timeout_seconds,
            transport=transport,
        )


__all__ = [
    "BinanceSpotMarketDataSource",
    "CoinbaseAdvancedTradeMarketDataSource",
    "NyFedMarketsDataSource",
    "OecdSdmxDataSource",
    "OkxMarketDataSource",
]
