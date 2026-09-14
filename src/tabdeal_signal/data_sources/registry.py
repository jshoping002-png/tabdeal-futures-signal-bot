"""Read-only source registration metadata.

This module describes source lifecycle and access boundaries only. It does not
perform network access, account operations, trading, or order execution.
"""

from dataclasses import dataclass
from enum import StrEnum


class SourceStatus(StrEnum):
    PLANNED = "planned"
    APPROVED = "approved"
    IMPLEMENTED = "implemented"
    VERIFIED = "verified"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class SourceRegistration:
    """Immutable metadata for one approved or proposed read-only source."""

    name: str
    category: str
    role: str
    status: SourceStatus = SourceStatus.PLANNED
    read_only: bool = True
    context_only: bool = False

    def __post_init__(self) -> None:
        for field_name in ("name", "category", "role"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        if not isinstance(self.status, SourceStatus):
            raise ValueError("status must be a SourceStatus")
        if not self.read_only:
            raise ValueError("source registrations must be read-only")


__all__ = ["SourceRegistration", "SourceStatus"]
