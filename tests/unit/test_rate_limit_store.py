"""Shared rate-limit storage health checks; backend details must not leak."""
import pytest

from app import verify_shared_rate_limit_storage


class FakeStorage:
    def __init__(self, error=None):
        self.error = error
        self.calls = 0

    def check(self):
        self.calls += 1
        if self.error:
            raise self.error


class FakeLimiter:
    def __init__(self, storage):
        self.storage = storage


def test_storage_probe_calls_backend_check():
    storage = FakeStorage()
    verify_shared_rate_limit_storage(FakeLimiter(storage))
    assert storage.calls == 1


def test_storage_probe_hides_backend_exception_details():
    storage = FakeStorage(RuntimeError("redis://user:secret@private-host"))
    with pytest.raises(RuntimeError, match="shared rate-limit storage is unavailable") as exc:
        verify_shared_rate_limit_storage(FakeLimiter(storage))
    assert "secret" not in str(exc.value) and "private-host" not in str(exc.value)


def test_storage_probe_fails_if_backend_has_no_health_check():
    with pytest.raises(RuntimeError, match="health check is unavailable"):
        verify_shared_rate_limit_storage(FakeLimiter(object()))


class PropertyFailureLimiter:
    @property
    def storage(self):
        raise RuntimeError("redis://user:secret@private-host failed to initialize")


def test_storage_probe_hides_errors_raised_while_accessing_storage_property():
    with pytest.raises(RuntimeError, match="shared rate-limit storage is unavailable") as exc:
        verify_shared_rate_limit_storage(PropertyFailureLimiter())
    assert "secret" not in str(exc.value)
    assert "private-host" not in str(exc.value)


def test_storage_probe_rejects_explicit_unhealthy_result():
    class UnhealthyStorage:
        def check(self):
            return False

    with pytest.raises(RuntimeError, match="shared rate-limit storage is unavailable"):
        verify_shared_rate_limit_storage(FakeLimiter(UnhealthyStorage()))
