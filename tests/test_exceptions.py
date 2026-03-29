"""Tests for exception classes."""

from validkit.exceptions import (
    ValidKitError,
    ValidKitAPIError,
    InvalidAPIKeyError,
    RateLimitError,
    BatchSizeError,
    TimeoutError,
    ConnectionError,
    InvalidEmailError,
    WebhookError,
    ConfigurationError,
)


class TestExceptionHierarchy:
    def test_all_inherit_from_validkit_error(self):
        assert issubclass(ValidKitAPIError, ValidKitError)
        assert issubclass(InvalidAPIKeyError, ValidKitAPIError)
        assert issubclass(RateLimitError, ValidKitAPIError)
        assert issubclass(BatchSizeError, ValidKitAPIError)
        assert issubclass(TimeoutError, ValidKitError)
        assert issubclass(ConnectionError, ValidKitError)
        assert issubclass(WebhookError, ValidKitError)
        assert issubclass(ConfigurationError, ValidKitError)


class TestRateLimitError:
    def test_stores_retry_info(self):
        e = RateLimitError(retry_after=30, limit=100, remaining=0, reset=1700000000)
        assert e.retry_after == 30
        assert e.limit == 100
        assert e.remaining == 0
        assert e.status_code == 429

    def test_default_message(self):
        e = RateLimitError()
        assert "Rate limit" in str(e)


class TestBatchSizeError:
    def test_stores_size_info(self):
        e = BatchSizeError(size=15000, max_size=10000)
        assert e.size == 15000
        assert e.max_size == 10000
        assert e.status_code == 400


class TestInvalidAPIKeyError:
    def test_default_message(self):
        e = InvalidAPIKeyError()
        assert e.status_code == 401
        assert "Invalid API key" in str(e)


class TestInvalidEmailError:
    def test_stores_email(self):
        e = InvalidEmailError(email="not-an-email")
        assert e.email == "not-an-email"
        assert e.status_code == 400


class TestValidKitAPIError:
    def test_str_format(self):
        e = ValidKitAPIError("Something failed", status_code=500, code="INTERNAL_ERROR")
        s = str(e)
        assert "Something failed" in s
        assert "500" in s
        assert "INTERNAL_ERROR" in s
