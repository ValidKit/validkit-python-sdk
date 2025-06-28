"""Async client for ValidKit API"""

import asyncio
import json
import time
from typing import Optional, Dict, Any, List, Union, Callable, AsyncIterator
from contextlib import asynccontextmanager
import aiohttp
from aiohttp import ClientSession, ClientTimeout, TCPConnector

from .config import ValidKitConfig
from .models import (
    EmailVerificationResult,
    BatchVerificationResult,
    BatchJob,
    CompactResult,
    ResponseFormat,
    BatchJobStatus
)
from .exceptions import (
    ValidKitAPIError,
    InvalidAPIKeyError,
    RateLimitError,
    BatchSizeError,
    TimeoutError,
    ConnectionError
)


class AsyncValidKit:
    """Async client for ValidKit API"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        config: Optional[ValidKitConfig] = None
    ):
        """Initialize the client
        
        Args:
            api_key: API key (can also be set via config)
            config: Full configuration object
        """
        if config:
            self.config = config
            if api_key:
                self.config.api_key = api_key
        else:
            if not api_key:
                raise ValueError("API key must be provided")
            self.config = ValidKitConfig(api_key=api_key)
        
        self._session: Optional[ClientSession] = None
        self._rate_limiter = RateLimiter(self.config.rate_limit) if self.config.rate_limit else None
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if not self._session:
            connector = TCPConnector(
                limit=self.config.max_connections,
                limit_per_host=self.config.max_keepalive_connections,
                enable_cleanup_closed=True
            )
            
            timeout = ClientTimeout(total=self.config.timeout)
            
            self._session = ClientSession(
                connector=connector,
                timeout=timeout,
                headers=self.config.headers
            )
    
    async def close(self):
        """Close the client session"""
        if self._session:
            await self._session.close()
            self._session = None
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """Make an API request with retries"""
        await self._ensure_session()
        
        if self._rate_limiter:
            await self._rate_limiter.acquire()
        
        url = f"{self.config.api_url}/{endpoint}"
        
        request_headers = self.config.headers.copy()
        if headers:
            request_headers.update(headers)
        
        try:
            async with self._session.request(
                method,
                url,
                json=json_data,
                headers=request_headers
            ) as response:
                # Extract rate limit headers
                rate_headers = {
                    'limit': response.headers.get('X-RateLimit-Limit'),
                    'remaining': response.headers.get('X-RateLimit-Remaining'),
                    'reset': response.headers.get('X-RateLimit-Reset')
                }
                
                response_data = await response.json()
                
                if response.status == 200:
                    return response_data
                
                # Handle errors
                if response.status == 401:
                    raise InvalidAPIKeyError(response_data.get('message', 'Invalid API key'))
                
                elif response.status == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    raise RateLimitError(
                        message=response_data.get('message', 'Rate limit exceeded'),
                        retry_after=retry_after,
                        limit=int(rate_headers['limit']) if rate_headers['limit'] else None,
                        remaining=int(rate_headers['remaining']) if rate_headers['remaining'] else None,
                        reset=int(rate_headers['reset']) if rate_headers['reset'] else None
                    )
                
                else:
                    raise ValidKitAPIError(
                        message=response_data.get('message', 'API error'),
                        status_code=response.status,
                        code=response_data.get('code'),
                        details=response_data
                    )
        
        except asyncio.TimeoutError:
            raise TimeoutError(f"Request timed out after {self.config.timeout} seconds")
        
        except aiohttp.ClientError as e:
            if retry_count < self.config.max_retries:
                # Exponential backoff
                await asyncio.sleep(2 ** retry_count)
                return await self._request(method, endpoint, json_data, headers, retry_count + 1)
            raise ConnectionError(f"Connection error: {str(e)}")
        
        except RateLimitError as e:
            if retry_count < self.config.max_retries and e.retry_after:
                await asyncio.sleep(e.retry_after)
                return await self._request(method, endpoint, json_data, headers, retry_count + 1)
            raise
    
    async def verify_email(
        self,
        email: str,
        format: ResponseFormat = ResponseFormat.FULL,
        trace_id: Optional[str] = None,
        debug: bool = False
    ) -> Union[EmailVerificationResult, CompactResult]:
        """Verify a single email address
        
        Args:
            email: Email address to verify
            format: Response format (full or compact)
            trace_id: Optional trace ID for multi-agent debugging
            debug: Enable debug mode for detailed validation steps
        
        Returns:
            Verification result with optional debug information
        """
        headers = {}
        if trace_id:
            headers['X-Trace-ID'] = trace_id
        
        data = {
            'email': email,
            'format': format.value if isinstance(format, ResponseFormat) else format,
            'debug': debug
        }
        
        response = await self._request('POST', 'verify', json_data=data, headers=headers)
        
        if format == ResponseFormat.COMPACT or self.config.compact_format:
            return CompactResult(**response['result'])
        else:
            return EmailVerificationResult(**response)
    
    async def verify_batch(
        self,
        emails: List[str],
        format: ResponseFormat = ResponseFormat.COMPACT,
        chunk_size: Optional[int] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        trace_id: Optional[str] = None,
        debug: bool = False
    ) -> Dict[str, Union[EmailVerificationResult, CompactResult]]:
        """Verify a batch of emails
        
        Args:
            emails: List of email addresses
            format: Response format
            chunk_size: Size of chunks to process
            progress_callback: Async callback for progress updates
            trace_id: Optional trace ID
            debug: Enable debug mode for detailed validation steps
        
        Returns:
            Dictionary mapping emails to results (with debug info if enabled)
        """
        if len(emails) > self.config.max_batch_size:
            raise BatchSizeError(len(emails), self.config.max_batch_size)
        
        chunk_size = chunk_size or self.config.default_chunk_size
        chunks = [emails[i:i + chunk_size] for i in range(0, len(emails), chunk_size)]
        
        all_results = {}
        processed = 0
        
        headers = {}
        if trace_id:
            headers['X-Trace-ID'] = trace_id
        
        for chunk in chunks:
            data = {
                'emails': chunk,
                'format': format.value if isinstance(format, ResponseFormat) else format,
                'debug': debug
            }
            
            response = await self._request('POST', 'verify/bulk/agent', json_data=data, headers=headers)
            
            # Parse results based on format
            if format == ResponseFormat.COMPACT:
                for email, result in response.get('results', {}).items():
                    all_results[email] = CompactResult(**result)
            else:
                for email, result in response.get('results', {}).items():
                    all_results[email] = EmailVerificationResult(**result)
            
            processed += len(chunk)
            
            if progress_callback:
                if asyncio.iscoroutinefunction(progress_callback):
                    await progress_callback(processed, len(emails))
                else:
                    progress_callback(processed, len(emails))
        
        return all_results
    
    async def verify_batch_async(
        self,
        emails: List[str],
        webhook_url: str,
        webhook_headers: Optional[Dict[str, str]] = None,
        format: ResponseFormat = ResponseFormat.COMPACT,
        trace_id: Optional[str] = None
    ) -> BatchJob:
        """Start an async batch verification job
        
        Args:
            emails: List of email addresses
            webhook_url: URL to receive results
            webhook_headers: Optional headers for webhook
            format: Response format
            trace_id: Optional trace ID
        
        Returns:
            Batch job information
        """
        if len(emails) > self.config.max_batch_size:
            raise BatchSizeError(len(emails), self.config.max_batch_size)
        
        headers = {}
        if trace_id:
            headers['X-Trace-ID'] = trace_id
        
        data = {
            'emails': emails,
            'format': format.value if isinstance(format, ResponseFormat) else format,
            'async': True,
            'webhook_url': webhook_url
        }
        
        if webhook_headers:
            data['webhook_headers'] = webhook_headers
        
        response = await self._request('POST', 'verify/bulk/agent', json_data=data, headers=headers)
        
        return BatchJob(**response['job'])
    
    async def get_batch_status(self, job_id: str) -> BatchJob:
        """Get status of a batch job
        
        Args:
            job_id: Batch job ID
        
        Returns:
            Updated batch job information
        """
        response = await self._request('GET', f'batch/{job_id}')
        return BatchJob(**response)
    
    async def cancel_batch(self, job_id: str) -> bool:
        """Cancel a batch job
        
        Args:
            job_id: Batch job ID
        
        Returns:
            True if cancelled successfully
        """
        response = await self._request('POST', f'batch/{job_id}/cancel')
        return response.get('success', False)
    
    async def stream_verify(
        self,
        emails: List[str],
        format: ResponseFormat = ResponseFormat.COMPACT,
        batch_size: int = 100
    ) -> AsyncIterator[Tuple[str, Union[EmailVerificationResult, CompactResult]]]:
        """Stream verification results as they complete
        
        Args:
            emails: List of email addresses
            format: Response format
            batch_size: Size of concurrent batches
        
        Yields:
            Tuples of (email, result)
        """
        semaphore = asyncio.Semaphore(10)  # Limit concurrent requests
        
        async def verify_with_semaphore(email: str):
            async with semaphore:
                try:
                    result = await self.verify_email(email, format)
                    return email, result
                except Exception as e:
                    # Return error as result
                    if format == ResponseFormat.COMPACT:
                        return email, CompactResult(v=False, r=str(e))
                    else:
                        return email, EmailVerificationResult(
                            success=False,
                            email=email,
                            valid=False
                        )
        
        # Create tasks in batches
        for i in range(0, len(emails), batch_size):
            batch = emails[i:i + batch_size]
            tasks = [verify_with_semaphore(email) for email in batch]
            
            # Yield results as they complete
            for coro in asyncio.as_completed(tasks):
                email, result = await coro
                yield email, result


class RateLimiter:
    """Simple rate limiter for API requests"""
    
    def __init__(self, rate_limit: int):
        """Initialize rate limiter
        
        Args:
            rate_limit: Requests per minute
        """
        self.rate_limit = rate_limit
        self.interval = 60.0 / rate_limit  # Seconds between requests
        self.last_request = 0.0
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire permission to make a request"""
        async with self._lock:
            now = time.time()
            time_since_last = now - self.last_request
            
            if time_since_last < self.interval:
                await asyncio.sleep(self.interval - time_since_last)
            
            self.last_request = time.time()