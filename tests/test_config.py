"""Tests for ValidKitConfig validation."""

import pytest
from validkit.config import ValidKitConfig


class TestConfigValidation:
    def test_requires_api_key(self):
        with pytest.raises(ValueError, match="API key"):
            ValidKitConfig(api_key="")

    def test_requires_valid_base_url(self):
        with pytest.raises(ValueError, match="Base URL"):
            ValidKitConfig(api_key="test", base_url="not-a-url")

    def test_requires_positive_timeout(self):
        with pytest.raises(ValueError, match="Timeout"):
            ValidKitConfig(api_key="test", timeout=0)

    def test_requires_non_negative_retries(self):
        with pytest.raises(ValueError, match="retries"):
            ValidKitConfig(api_key="test", max_retries=-1)

    def test_requires_positive_rate_limit(self):
        with pytest.raises(ValueError, match="Rate limit"):
            ValidKitConfig(api_key="test", rate_limit=0)

    def test_rate_limit_none_is_valid(self):
        config = ValidKitConfig(api_key="test", rate_limit=None)
        assert config.rate_limit is None

    def test_defaults(self):
        config = ValidKitConfig(api_key="test_key")
        assert config.base_url == "https://api.validkit.com"
        assert config.api_version == "v1"
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.compact_format is True

    def test_user_agent_contains_version(self):
        config = ValidKitConfig(api_key="test")
        assert "1.1.3" in config.user_agent

    def test_headers_include_sdk_version(self):
        config = ValidKitConfig(api_key="test")
        assert config.headers["X-SDK-Version"] == "1.1.3"
        assert config.headers["X-SDK-Language"] == "python"
