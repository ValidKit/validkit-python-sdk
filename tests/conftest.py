"""Shared fixtures for ValidKit SDK tests."""

import pytest
from unittest.mock import AsyncMock, patch
from validkit import AsyncValidKit, ValidKit
from validkit.config import ValidKitConfig


@pytest.fixture
def api_key():
    return "vk_test_abc123"


@pytest.fixture
def config(api_key):
    return ValidKitConfig(api_key=api_key)


@pytest.fixture
def client(api_key):
    return AsyncValidKit(api_key=api_key)


@pytest.fixture
def sync_client(mock_request):
    """Create a sync ValidKit client with mocked HTTP."""
    client = ValidKit(api_key="vk_test_abc123")
    yield client
    client.close()


@pytest.fixture
def mock_request():
    """Patch AsyncValidKit._request to capture calls without making HTTP requests."""
    with patch.object(AsyncValidKit, '_request', new_callable=AsyncMock) as mock:
        yield mock
