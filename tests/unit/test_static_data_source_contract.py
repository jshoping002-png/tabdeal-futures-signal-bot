from inspect import signature

from tabdeal_signal.data_sources.contracts import ReadOnlyDataSource
from tabdeal_signal.data_sources.static import StaticDataSource


def test_static_data_source_implements_read_only_contract() -> None:
    implementation_signature = signature(StaticDataSource.fetch_snapshot)

    assert hasattr(StaticDataSource, "fetch_snapshot")
    assert not any(
        name in dir(StaticDataSource)
        for name in ("place_order", "execute_trade", "cancel_order")
    )
    assert list(implementation_signature.parameters) == ["self", "as_of"]


def test_static_data_source_fetch_signature_matches_contract() -> None:
    contract_signature = signature(ReadOnlyDataSource.fetch_snapshot)
    implementation_signature = signature(StaticDataSource.fetch_snapshot)

    assert list(implementation_signature.parameters) == list(
        contract_signature.parameters
    )
    assert implementation_signature.parameters["as_of"].default is None
