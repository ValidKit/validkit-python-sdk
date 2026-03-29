"""Tests for AsyncValidKit client.

Verifies URL construction, HTTP methods, auth headers, and request/response
handling without making real HTTP calls.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from validkit.client import AsyncValidKit
from validkit.config import ValidKitConfig
from validkit.models import (
    EmailVerificationResult,
    CompactResult,
    BatchJob,
    BatchVerificationResult,
    BatchJobStatus,
    ResponseFormat,
)
from validkit.exceptions import (
    BatchSizeError,
)


class TestClientInit:
    def test_requires_api_key(self):
        with pytest.raises(ValueError, match="API key"):
            AsyncValidKit()

    def test_accepts_api_key_string(self):
        client = AsyncValidKit(api_key="vk_test_123")
        assert client.config.api_key == "vk_test_123"

    def test_accepts_config_object(self):
        config = ValidKitConfig(api_key="vk_test_456", timeout=60)
        client = AsyncValidKit(config=config)
        assert client.config.api_key == "vk_test_456"
        assert client.config.timeout == 60

    def test_api_key_overrides_config(self):
        config = ValidKitConfig(api_key="from_config")
        client = AsyncValidKit(api_key="from_param", config=config)
        assert client.config.api_key == "from_param"


class TestURLConstruction:
    def test_default_api_url(self):
        config = ValidKitConfig(api_key="test")
        assert config.api_url == "https://api.validkit.com/api/v1"

    def test_custom_base_url(self):
        config = ValidKitConfig(api_key="test", base_url="https://custom.api.com")
        assert config.api_url == "https://custom.api.com/api/v1"

    def test_trailing_slash_stripped(self):
        config = ValidKitConfig(api_key="test", base_url="https://api.validkit.com/")
        assert config.api_url == "https://api.validkit.com/api/v1"


class TestAuthHeaders:
    def test_sends_api_key_header(self):
        config = ValidKitConfig(api_key="vk_test_secret")
        headers = config.headers
        assert headers["X-API-Key"] == "vk_test_secret"

    def test_sends_user_agent(self):
        config = ValidKitConfig(api_key="test")
        assert "ValidKit-Python" in config.headers["User-Agent"]

    def test_sends_json_content_type(self):
        config = ValidKitConfig(api_key="test")
        assert config.headers["Content-Type"] == "application/json"


class TestVerifyEmail:
    """Tests for verify_email.

    Note: default config has compact_format=True, so verify_email always
    takes the compact response path (expects response['result']).
    Tests use compact-shaped mock responses to match this behavior.
    """

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, client, mock_request):
        mock_request.return_value = {"result": {"v": True}}
        await client.verify_email("test@example.com")
        mock_request.assert_called_once()
        args = mock_request.call_args
        assert args[0][0] == "POST"
        assert args[0][1] == "verify"

    @pytest.mark.asyncio
    async def test_returns_compact_result_by_default(self, client, mock_request):
        mock_request.return_value = {"result": {"v": True, "d": False}}
        result = await client.verify_email("user@test.com")
        assert isinstance(result, CompactResult)
        assert result.v is True

    @pytest.mark.asyncio
    async def test_full_format_with_compact_disabled(self, mock_request):
        """When compact_format=False and format=FULL, returns EmailVerificationResult."""
        client = AsyncValidKit(
            config=ValidKitConfig(api_key="test", compact_format=False)
        )
        mock_request.return_value = {
            "success": True,
            "email": "t@t.com",
            "valid": True,
        }
        result = await client.verify_email("t@t.com")
        assert isinstance(result, EmailVerificationResult)
        assert result.email == "t@t.com"

    @pytest.mark.asyncio
    async def test_passes_trace_id(self, client, mock_request):
        mock_request.return_value = {"result": {"v": True}}
        await client.verify_email("t@t.com", trace_id="trace-123")
        call_args = mock_request.call_args
        headers = call_args.kwargs.get("headers") or call_args[1].get("headers", {})
        assert headers.get("X-Trace-ID") == "trace-123"


class TestVerifyBatch:
    @pytest.mark.asyncio
    async def test_calls_agent_bulk_endpoint(self, client, mock_request):
        mock_request.return_value = {
            "results": {"a@b.com": {"v": True}},
        }
        await client.verify_batch(["a@b.com"])
        args = mock_request.call_args
        assert args[0][0] == "POST"
        assert args[0][1] == "verify/bulk/agent"

    @pytest.mark.asyncio
    async def test_rejects_oversized_batch(self, client, mock_request):
        emails = [f"user{i}@test.com" for i in range(10001)]
        with pytest.raises(BatchSizeError):
            await client.verify_batch(emails)


class TestGetBatchStatus:
    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, client, mock_request):
        now = datetime.now().isoformat()
        mock_request.return_value = {
            "id": "batch-abc",
            "status": "processing",
            "total_emails": 100,
            "processed": 50,
            "created_at": now,
            "updated_at": now,
        }
        result = await client.get_batch_status("batch-abc")
        args = mock_request.call_args
        assert args[0][0] == "GET"
        assert args[0][1] == "batch/batch-abc"
        assert isinstance(result, BatchJob)


class TestCancelBatch:
    """Tests for cancel_batch — regression tests for #2316.

    The original bug: SDK sent POST to /batch/{id}/cancel.
    The API expects: DELETE to /batch/{id}.
    """

    @pytest.mark.asyncio
    async def test_uses_delete_method(self, client, mock_request):
        """cancel_batch MUST use DELETE, not POST (#2316)."""
        now = datetime.now().isoformat()
        mock_request.return_value = {
            "id": "batch-abc",
            "status": "cancelled",
            "total_emails": 100,
            "processed": 50,
            "created_at": now,
            "updated_at": now,
        }
        await client.cancel_batch("batch-abc")
        args = mock_request.call_args
        assert args[0][0] == "DELETE", (
            f"cancel_batch must use DELETE, got {args[0][0]}. "
            "See #2316: API route is DELETE /v1/batch/:batchId"
        )

    @pytest.mark.asyncio
    async def test_calls_correct_path(self, client, mock_request):
        """cancel_batch path must be batch/{id}, not batch/{id}/cancel."""
        now = datetime.now().isoformat()
        mock_request.return_value = {
            "id": "batch-xyz",
            "status": "cancelled",
            "total_emails": 10,
            "processed": 5,
            "created_at": now,
            "updated_at": now,
        }
        await client.cancel_batch("batch-xyz")
        args = mock_request.call_args
        assert args[0][1] == "batch/batch-xyz", (
            f"cancel_batch path must be 'batch/batch-xyz', got '{args[0][1]}'. "
            "See #2316: no /cancel suffix"
        )

    @pytest.mark.asyncio
    async def test_returns_batch_job(self, client, mock_request):
        now = datetime.now().isoformat()
        mock_request.return_value = {
            "id": "batch-abc",
            "status": "cancelled",
            "total_emails": 100,
            "processed": 50,
            "created_at": now,
            "updated_at": now,
        }
        result = await client.cancel_batch("batch-abc")
        assert isinstance(result, BatchJob)
        assert result.status == BatchJobStatus.CANCELLED


class TestGetBatchResults:
    """Tests for get_batch_results — regression tests for #2317.

    This method was entirely missing from the original SDK.
    The API has GET /v1/batch/:batchId/results.
    """

    @pytest.mark.asyncio
    async def test_method_exists(self, client):
        """get_batch_results must exist on AsyncValidKit (#2317)."""
        assert hasattr(client, "get_batch_results"), (
            "AsyncValidKit is missing get_batch_results(). See #2317."
        )

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, client, mock_request):
        mock_request.return_value = {
            "success": True,
            "total": 2,
            "valid": 1,
            "invalid": 1,
            "results": {
                "a@b.com": {"v": True},
                "c@d.com": {"v": False, "r": "invalid"},
            },
        }
        result = await client.get_batch_results("batch-abc")
        args = mock_request.call_args
        assert args[0][0] == "GET"
        assert args[0][1] == "batch/batch-abc/results"

    @pytest.mark.asyncio
    async def test_returns_batch_verification_result(self, client, mock_request):
        mock_request.return_value = {
            "success": True,
            "total": 1,
            "valid": 1,
            "invalid": 0,
            "results": {"a@b.com": {"v": True}},
        }
        result = await client.get_batch_results("batch-abc")
        assert isinstance(result, BatchVerificationResult)
        assert result.total == 1
