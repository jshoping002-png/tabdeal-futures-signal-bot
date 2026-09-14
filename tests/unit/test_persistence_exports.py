from tabdeal_signal.persistence import (
    DecisionPersistence,
    PersistenceRequest,
    PersistenceResult,
    SQLiteDecisionPersistence,
)
from tabdeal_signal.persistence import __all__ as persistence_exports
from tabdeal_signal.persistence.contracts import (
    DecisionPersistence as module_protocol,
    PersistenceRequest as module_request,
    PersistenceResult as module_result,
)
from tabdeal_signal.persistence.sqlite import SQLiteDecisionPersistence as module_sqlite


def test_persistence_package_exports_match_implementation_symbols() -> None:
    assert DecisionPersistence is module_protocol
    assert PersistenceRequest is module_request
    assert PersistenceResult is module_result
    assert SQLiteDecisionPersistence is module_sqlite


def test_persistence_package_exports_are_usable_symbols() -> None:
    assert getattr(DecisionPersistence, "persist")
    assert PersistenceRequest is not None
    assert PersistenceResult is not None
    assert callable(SQLiteDecisionPersistence)


def test_persistence_package_exports_are_explicit_and_stable() -> None:
    assert persistence_exports == [
        "DecisionPersistence",
        "PersistenceRequest",
        "PersistenceResult",
        "SQLiteDecisionPersistence",
    ]
