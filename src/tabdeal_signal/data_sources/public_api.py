"""Operational read-only source API for existing reports 001-2040.

This module is separate from ``tabdeal_signal.data_sources.__init__`` because the
latter is a deliberately stable public compatibility surface. No new sources,
strategy rules, trading operations, or credentials are introduced here.
"""

from .adapter_catalog import (
    AdapterBinding,
    VERIFIED_ADAPTER_BINDINGS,
    adapter_bindings_for,
    resolve_adapter_class,
    source_ids_with_adapters,
)
from .endpoint_contracts import (
    EndpointContract,
    EndpointExactness,
    VERIFIED_ENDPOINT_CONTRACTS,
    endpoint_contracts_for,
    source_ids_with_endpoint_contracts,
)
from .endpoint_contract_validation import (
    EndpointValidationResult,
    endpoint_catalog_counts,
    validate_endpoint_catalog,
)
from .operational_manifest import (
    SOURCE_OPERATIONAL_MANIFEST,
    SourceOperationalManifest,
    operational_manifest_counts,
    operational_manifest_for,
    validate_operational_manifest,
)
from .replay import FIXTURE_FORMAT_VERSION, ReplayFixtureDataSource, SnapshotFixtureCodec
from .runtime_config import (
    KNOWN_RUNTIME_SOURCE_HOSTS,
    RUNTIME_CONFIGURED_SOURCE_IDS,
    RuntimeEndpointConfig,
    explicit_runtime_endpoint_config,
    runtime_endpoint_config,
)
from .runtime_source_factory import build_runtime_source
from .source_access import (
    SourceAccessSpec,
    SourceLifecycle,
    VERIFIED_SOURCE_ACCESS_SPECS,
    get_source_access_spec,
    source_ids,
)
from .source_adapter_validation import (
    AdapterValidationResult,
    source_adapter_validation_counts,
    validate_source_adapter_catalog,
)
from .source_readiness import (
    ReadinessGate,
    SourceReadiness,
    all_source_readiness,
    source_readiness_counts,
    source_readiness_for,
)


__all__ = [
    "AdapterBinding",
    "AdapterValidationResult",
    "EndpointContract",
    "EndpointExactness",
    "EndpointValidationResult",
    "FIXTURE_FORMAT_VERSION",
    "KNOWN_RUNTIME_SOURCE_HOSTS",
    "ReadinessGate",
    "ReplayFixtureDataSource",
    "RUNTIME_CONFIGURED_SOURCE_IDS",
    "RuntimeEndpointConfig",
    "SOURCE_OPERATIONAL_MANIFEST",
    "SourceAccessSpec",
    "SourceLifecycle",
    "SourceOperationalManifest",
    "SourceReadiness",
    "SnapshotFixtureCodec",
    "VERIFIED_ADAPTER_BINDINGS",
    "VERIFIED_ENDPOINT_CONTRACTS",
    "VERIFIED_SOURCE_ACCESS_SPECS",
    "adapter_bindings_for",
    "all_source_readiness",
    "build_runtime_source",
    "endpoint_catalog_counts",
    "endpoint_contracts_for",
    "explicit_runtime_endpoint_config",
    "get_source_access_spec",
    "operational_manifest_counts",
    "operational_manifest_for",
    "resolve_adapter_class",
    "runtime_endpoint_config",
    "source_adapter_validation_counts",
    "source_ids",
    "source_ids_with_adapters",
    "source_ids_with_endpoint_contracts",
    "source_readiness_counts",
    "source_readiness_for",
    "validate_endpoint_catalog",
    "validate_operational_manifest",
    "validate_source_adapter_catalog",
]
