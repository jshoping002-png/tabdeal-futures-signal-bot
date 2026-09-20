from datetime import datetime, timedelta, timezone

import pytest

from tabdeal_signal.persistence.reliability import OutboxLease


def make_lease() -> OutboxLease:
    acquired = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    return OutboxLease(
        event_id="event-1",
        lease_token="lease-1",
        owner_id="worker-1",
        acquired_at=acquired,
        expires_at=acquired + timedelta(minutes=1),
    )


def test_lease_requires_identity_fields() -> None:
    acquired = make_lease().acquired_at
    expires = make_lease().expires_at
    for field, values in (
        ("event_id", ("", "lease-1", "worker-1")),
        ("lease_token", ("event-1", "", "worker-1")),
        ("owner_id", ("event-1", "lease-1", "")),
    ):
        with pytest.raises(ValueError, match=field):
            OutboxLease(*values, acquired, expires)


def test_lease_requires_datetime_timestamps() -> None:
    lease = make_lease()
    with pytest.raises(ValueError, match="acquired_at must be a datetime"):
        OutboxLease("event-1", "lease-1", "worker-1", object(), lease.expires_at)
    with pytest.raises(ValueError, match="expires_at must be a datetime"):
        OutboxLease("event-1", "lease-1", "worker-1", lease.acquired_at, object())


def test_lease_requires_timezone_aware_ordered_timestamps() -> None:
    acquired = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="timezone-aware"):
        OutboxLease("event-1", "lease-1", "worker-1", acquired.replace(tzinfo=None), acquired)

    with pytest.raises(ValueError, match="after"):
        OutboxLease("event-1", "lease-1", "worker-1", acquired, acquired)

    with pytest.raises(ValueError, match="same timezone"):
        OutboxLease("event-1", "lease-1", "worker-1", acquired, acquired.replace(tzinfo=timezone(timedelta(hours=1))))


def test_lease_expiry_is_strictly_at_or_after_expiration() -> None:
    lease = make_lease()
    before = lease.expires_at - timedelta(microseconds=1)
    assert lease.is_expired_at(before) is False
    assert lease.is_expired_at(lease.expires_at) is True


def test_lease_rejects_invalid_reference_time() -> None:
    lease = make_lease()
    with pytest.raises(ValueError, match="reference_time"):
        lease.is_expired_at(object())

    with pytest.raises(ValueError, match="timezone-aware"):
        lease.is_expired_at(lease.expires_at.replace(tzinfo=None))

    with pytest.raises(ValueError, match="lease timezone"):
        lease.is_expired_at(lease.expires_at.replace(tzinfo=timezone(timedelta(hours=1))))


def test_lease_rejects_reference_before_acquisition() -> None:
    lease = make_lease()
    with pytest.raises(ValueError, match="precede lease acquisition"):
        lease.is_expired_at(lease.acquired_at - timedelta(seconds=1))
