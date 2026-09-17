from tabdeal_signal.data_sources.adapter_catalog import (
    VERIFIED_ADAPTER_BINDINGS,
    resolve_adapter_class,
)


def test_every_declared_adapter_class_resolves_from_its_binding():
    assert VERIFIED_ADAPTER_BINDINGS
    for binding in VERIFIED_ADAPTER_BINDINGS:
        adapter = resolve_adapter_class(binding.source_id, binding.class_name)
        assert isinstance(adapter, type)
        assert adapter.__name__ == binding.class_name
