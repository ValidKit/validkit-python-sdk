"""Tests for synchronous ValidKit client.

Mirrors test_client.py patterns — mocks AsyncValidKit._request to
verify the sync wrapper delegates correctly without making HTTP calls.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime

from validkit import ValidKit
from validkit.client import AsyncValidKit
from validkit.config import ValidKitConfig
from validkit.models import (
    CompactResult,
    EmailVerificationResult,
    BatchJob,
    BatchVerificationResult,
    BatchJobStatus,
    ResponseFormat,
)
from validkit.exceptions import BatchSizeError


class TestSyncClientInit:
    def test_requires_api_key(self):
        with pytest.raises(ValueError, match="API key"):
            ValidKit()

    def test_accepts_api_key_string(self, mock_request):
        client = ValidKit(api_key="vk_test_123")
        assert client._async_client.config.api_key == "vk_test_123"
        client.close()

    def test_accepts_config_object(self, mock_request):
        config = ValidKitConfig(api_key="vk_test_456", timeout=60)
        client = ValidKit(config=config)
        assert client._async_client.config.timeout == 60
        client.close()


class TestSyncVerify:
    def test_returns_compact_result(self, sync_client, mock_request):
        mock_request.return_value = {"result": {"v": True, "d": False}}
        result = sync_client.verify("user@test.com")
        assert isinstance(result, CompactResult)
        assert result.v is True

    def test_calls_correct_endpoint(self, sync_client, mock_request):
        mock_request.return_value = {"result": {"v": True}}
        sync_client.verify("test@example.com")
        mock_request.assert_called_once()
        args = mock_request.call_args
        assert args[0][0] == "POST"
        assert args[0][1] == "verify"

    def test_full_format_with_compact_disabled(self, mock_request):
        config = ValidKitConfig(api_key="test", compact_format=False)
        client = ValidKit(config=config)
        mock_request.return_value = {
            "success": True,
            "email": "t@t.com",
            "valid": True,
        }
        result = client.verify("t@t.com")
        assert isinstance(result, EmailVerificationResult)
        client.close()


class TestSyncVerifyBatch:
    def test_calls_agent_bulk_endpoint(self, sync_client, mock_request):
        mock_request.return_value = {
            "results": {"a@b.com": {"v": True}},
        }
        sync_client.verify_batch(["a@b.com"])
        args = mock_request.call_args
        assert args[0][0] == "POST"
        assert args[0][1] == "verify/bulk/agent"

    def test_rejects_oversized_batch(self, sync_client, mock_request):
        emails = [f"user{i}@test.com" for i in range(10001)]
        with pytest.raises(BatchSizeError):
            sync_client.verify_batch(emails)

    def test_rejects_async_progress_callback(self, sync_client, mock_request):
        async def bad_callback(processed, total):
            pass

        with pytest.raises(TypeError, match="plain function"):
            sync_client.verify_batch(["a@b.com"], progress_callback=bad_callback)

    def test_sync_progress_callback(self, sync_client, mock_request):
        mock_request.return_value = {
            "results": {"a@b.com": {"v": True}},
        }
        called = []

        def callback(processed, total):
            called.append((processed, total))

        sync_client.verify_batch(["a@b.com"], progress_callback=callback)
        assert len(called) == 1
        assert called[0] == (1, 1)


class TestSyncBatchLifecycle:
    def _batch_job_response(self, status="processing"):
        now = datetime.now().isoformat()
        return {
            "id": "batch-abc",
            "status": status,
            "total_emails": 100,
            "processed": 50,
            "created_at": now,
            "updated_at": now,
        }

    def test_get_batch_status(self, sync_client, mock_request):
        mock_request.return_value = self._batch_job_response("processing")
        result = sync_client.get_batch_status("batch-abc")
        assert isinstance(result, BatchJob)
        args = mock_request.call_args
        assert args[0][0] == "GET"
        assert args[0][1] == "batch/batch-abc"

    def test_get_batch_results(self, sync_client, mock_request):
        mock_request.return_value = {
            "success": True,
            "total": 1,
            "valid": 1,
            "invalid": 0,
            "results": {"a@b.com": {"v": True}},
        }
        result = sync_client.get_batch_results("batch-abc")
        assert isinstance(result, BatchVerificationResult)
        args = mock_request.call_args
        assert args[0][0] == "GET"
        assert args[0][1] == "batch/batch-abc/results"

    def test_cancel_batch_uses_delete(self, sync_client, mock_request):
        """Regression: cancel_batch must use DELETE (#2316)."""
        mock_request.return_value = self._batch_job_response("cancelled")
        sync_client.cancel_batch("batch-abc")
        args = mock_request.call_args
        assert args[0][0] == "DELETE"


class TestSyncContextManager:
    def test_with_statement(self, mock_request):
        mock_request.return_value = {"result": {"v": True}}
        with ValidKit(api_key="vk_test_123") as client:
            result = client.verify("test@example.com")
            assert result.v is True
        # After exiting, the runner thread should be stopped

    def test_close_is_idempotent(self, mock_request):
        client = ValidKit(api_key="vk_test_123")
        client.close()
        # Second close should not raise
        client.close()


class TestNestedEventLoop:
    def test_works_inside_existing_event_loop(self, mock_request):
        """ValidKit must work when an event loop is already running.

        This is the critical test for Jupyter / Django compatibility.
        We simulate an outer loop by running the test body inside one.
        """
        mock_request.return_value = {"result": {"v": True}}

        async def _inner():
            # An event loop is now running on THIS thread.
            client = ValidKit(api_key="vk_test_123")
            result = client.verify("test@example.com")
            assert result.v is True
            client.close()

        asyncio.run(_inner())
