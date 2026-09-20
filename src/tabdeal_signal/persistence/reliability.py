from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class OutboxLease:
    """Immutable ownership record for one leased outbox delivery."""

    event_id: str
    lease_token: str
    owner_id: str
    acquired_at: datetime
    expires_at: datetime

    def __post_init__(self) -> None:
        for name in ("event_id", "lease_token", "owner_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required")
        if not isinstance(self.acquired_at, datetime):
            raise ValueError("acquired_at must be a datetime")
        if not isinstance(self.expires_at, datetime):
            raise ValueError("expires_at must be a datetime")
        if (
            self.acquired_at.tzinfo is None
            or self.acquired_at.utcoffset() is None
            or self.expires_at.tzinfo is None
            or self.expires_at.utcoffset() is None
        ):
            raise ValueError("lease timestamps must be timezone-aware")
        if self.acquired_at.tzinfo != self.expires_at.tzinfo:
            raise ValueError("lease timestamps must use the same timezone")
        if self.expires_at <= self.acquired_at:
            raise ValueError("expires_at must be after acquired_at")

    def is_expired_at(self, reference_time: datetime) -> bool:
        if not isinstance(reference_time, datetime):
            raise ValueError("reference_time must be a datetime")
        if reference_time.tzinfo is None or reference_time.utcoffset() is None:
            raise ValueError("reference_time must be timezone-aware")
        if reference_time.tzinfo != self.expires_at.tzinfo:
            raise ValueError("reference_time must use the lease timezone")
        if reference_time < self.acquired_at:
            raise ValueError("reference_time cannot precede lease acquisition")
        return reference_time >= self.expires_at


class OutboxLeaseRepository(Protocol):
    """Storage boundary for exclusive, restart-safe outbox ownership."""

    def acquire_lease(
        self,
        *,
        event_id: str,
        owner_id: str,
        acquired_at: datetime,
        expires_at: datetime,
    ) -> OutboxLease | None:
        """Return a lease only when ownership can be acquired safely."""
        ...

    def release_lease(self, lease: OutboxLease) -> None:
        """Release only the exact lease represented by its token."""
        ...
