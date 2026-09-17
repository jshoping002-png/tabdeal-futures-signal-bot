"""Concrete import bindings for the read-only adapters recorded in source access.

This registry proves only that each declared adapter class has a stable module binding.
It does not promote a source to LIVE_VERIFIED, PRODUCTION_READY, or ACTIVE.
"""
from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import TypeAlias

from .source_access import VERIFIED_SOURCE_ACCESS_SPECS


AdapterClass: TypeAlias = type[object]


@dataclass(frozen=True, slots=True)
class AdapterBinding:
    source_id: str
    class_name: str
    module_path: str

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError("source_id must be non-empty")
        if not self.class_name.strip():
            raise ValueError("class_name must be non-empty")
        if not self.module_path.strip():
            raise ValueError("module_path must be non-empty")


_CLASS_MODULES: dict[str, str] = {
    "BinanceCoinMContinuousKlineDataSource": ".binance_coinm",
    "BybitKlineDataSource": ".bybit_kline",
    "BybitOrderbookDataSource": ".bybit",
    "BybitOpenInterestDataSource": ".bybit_open_interest",
    "BybitFundingRateDataSource": ".bybit_funding",
    "BybitTickersDataSource": ".bybit_tickers",
    "BybitInstrumentsInfoDataSource": ".bybit_instruments",
    "BlsPublicApiDataSource": ".public_sources",
    "BinanceSpotMarketDataSource": ".source_family_adapters",
    "TreasuryDailyRatesDataSource": ".public_sources",
    "SecEdgarDataSource": ".public_sources",
    "OkxMarketDataSource": ".source_family_adapters",
    "KrakenFuturesPublicCandleDataSource": ".kraken_futures",
    "CoinbaseAdvancedTradeMarketDataSource": ".source_family_adapters",
    "DeribitPublicMarketDataSource": ".deribit_public",
    "CftcPublicReportingDataSource": ".public_sources",
    "CoinMarketCapKeylessDataSource": ".public_sources",
    "EcbSdmxDataSource": ".public_sources",
    "BisStatisticsDataSource": ".public_sources",
    "EurostatDataSource": ".public_sources",
    "OecdSdmxDataSource": ".source_family_adapters",
    "NyFedMarketsDataSource": ".source_family_adapters",
}


def _bindings() -> tuple[AdapterBinding, ...]:
    missing = sorted(
        {
            class_name
            for spec in VERIFIED_SOURCE_ACCESS_SPECS
            for class_name in spec.adapter_classes
            if class_name not in _CLASS_MODULES
        }
    )
    if missing:
        raise ValueError(f"missing module bindings: {missing}")
    return tuple(
        AdapterBinding(spec.source_id, class_name, _CLASS_MODULES[class_name])
        for spec in VERIFIED_SOURCE_ACCESS_SPECS
        for class_name in spec.adapter_classes
    )


VERIFIED_ADAPTER_BINDINGS: tuple[AdapterBinding, ...] = _bindings()


def adapter_bindings_for(source_id: str) -> tuple[AdapterBinding, ...]:
    if not isinstance(source_id, str) or not source_id.strip():
        raise ValueError("source_id must be non-empty")
    normalized = source_id.strip()
    return tuple(binding for binding in VERIFIED_ADAPTER_BINDINGS if binding.source_id == normalized)


def resolve_adapter_class(source_id: str, class_name: str) -> AdapterClass:
    for binding in adapter_bindings_for(source_id):
        if binding.class_name == class_name:
            module = import_module(binding.module_path, package=__package__)
            adapter = getattr(module, class_name, None)
            if adapter is None:
                raise LookupError(f"adapter class not found: {class_name}")
            if not isinstance(adapter, type):
                raise TypeError(f"adapter binding is not a class: {class_name}")
            return adapter
    raise KeyError((source_id, class_name))


def source_ids_with_adapters() -> tuple[str, ...]:
    return tuple(dict.fromkeys(binding.source_id for binding in VERIFIED_ADAPTER_BINDINGS))


__all__ = [
    "AdapterBinding",
    "VERIFIED_ADAPTER_BINDINGS",
    "adapter_bindings_for",
    "resolve_adapter_class",
    "source_ids_with_adapters",
]
