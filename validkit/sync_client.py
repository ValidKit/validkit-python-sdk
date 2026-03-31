"""Synchronous client for ValidKit API.

Wraps AsyncValidKit in a dedicated background event loop so callers
never need to write ``async`` / ``await``.  Safe to use inside Jupyter
notebooks, Django views, and other contexts where an event loop may
already be running.
"""

import asyncio
import threading
from typing import Optional, Dict, List, Union, Callable

from .client import AsyncValidKit
from .config import ValidKitConfig
from .models import (
    EmailVerificationResult,
    BatchVerificationResult,
    BatchJob,
    CompactResult,
    ResponseFormat,
)


class _SyncRunner:
    """Run coroutines synchronously via a background thread's event loop."""

    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._loop.run_forever, daemon=True
        )
        self._thread.start()

    def run(self, coro):
        """Submit *coro* to the background loop and block until it resolves."""
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    def close(self) -> None:
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=5)


class ValidKit:
    """Synchronous client for ValidKit email verification.

    Usage::

        from validkit import ValidKit

        client = ValidKit("YOUR_API_KEY")
        result = client.verify("user@example.com")
        print(result.v)      # True / False
        client.close()

    Or as a context manager::

        with ValidKit("YOUR_API_KEY") as client:
            result = client.verify("user@example.com")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        config: Optional[ValidKitConfig] = None,
    ):
        self._closed = False
        self._runner = _SyncRunner()
        self._async_client = AsyncValidKit(api_key=api_key, config=config)
        # Eagerly create the aiohttp session inside the background loop
        self._runner.run(self._async_client._ensure_session())

    # -- context manager -------------------------------------------------

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # -- public API ------------------------------------------------------

    def verify(
        self,
        email: str,
        format: ResponseFormat = ResponseFormat.FULL,
    ) -> Union[EmailVerificationResult, CompactResult]:
        """Verify a single email address.

        Args:
            email: Email address to verify.
            format: Response format (``FULL`` or ``COMPACT``).

        Returns:
            Verification result.
        """
        return self._runner.run(
            self._async_client.verify_email(email, format=format)
        )

    def verify_batch(
        self,
        emails: List[str],
        format: ResponseFormat = ResponseFormat.COMPACT,
        chunk_size: Optional[int] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Dict[str, Union[EmailVerificationResult, CompactResult]]:
        """Verify a batch of emails (up to 10 000).

        Args:
            emails: List of email addresses.
            format: Response format.
            chunk_size: Number of emails per chunk (default 1 000).
            progress_callback: ``fn(processed, total)`` called after each chunk.
                Must be a plain function, not an async coroutine.

        Returns:
            Dictionary mapping each email to its result.
        """
        if progress_callback and asyncio.iscoroutinefunction(progress_callback):
            raise TypeError(
                "progress_callback must be a plain function, not async. "
                "Use AsyncValidKit for async callbacks."
            )
        return self._runner.run(
            self._async_client.verify_batch(
                emails,
                format=format,
                chunk_size=chunk_size,
                progress_callback=progress_callback,
            )
        )

    def get_batch_status(self, job_id: str) -> BatchJob:
        """Get status of an async batch job."""
        return self._runner.run(
            self._async_client.get_batch_status(job_id)
        )

    def get_batch_results(self, job_id: str) -> BatchVerificationResult:
        """Get results of a completed batch job."""
        return self._runner.run(
            self._async_client.get_batch_results(job_id)
        )

    def cancel_batch(self, job_id: str) -> BatchJob:
        """Cancel a batch job."""
        return self._runner.run(
            self._async_client.cancel_batch(job_id)
        )

    def close(self) -> None:
        """Close the client and release resources.

        Safe to call multiple times.
        """
        if self._closed:
            return
        self._closed = True
        self._runner.run(self._async_client.close())
        self._runner.close()
