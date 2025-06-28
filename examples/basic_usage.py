"""Basic usage examples for ValidKit Python SDK"""

import asyncio
from validkit import AsyncValidKit, EmailVerificationResult, CompactResult


async def single_email_example():
    """Example: Verify a single email"""
    print("=== Single Email Verification ===")
    
    async with AsyncValidKit(api_key="your_api_key") as client:
        # Full format response
        result = await client.verify_email("john.doe@gmail.com")
        print(f"Email: {result.email}")
        print(f"Valid: {result.valid}")
        print(f"Format valid: {result.format.valid}")
        print(f"Disposable: {result.disposable.value}")
        print(f"MX records: {result.mx.records}")
        print()
        
        # Compact format (for token efficiency)
        compact = await client.verify_email("test@example.com", format="compact")
        print(f"Compact result: Valid={compact.v}, Disposable={compact.d}")


async def batch_verification_example():
    """Example: Verify multiple emails"""
    print("\n=== Batch Email Verification ===")
    
    emails = [
        "valid@gmail.com",
        "invalid.email",
        "disposable@tempmail.com",
        "test@example.com",
        "user@company.com"
    ]
    
    async with AsyncValidKit(api_key="your_api_key") as client:
        results = await client.verify_batch(emails)
        
        for email, result in results.items():
            if isinstance(result, CompactResult):
                status = "✓" if result.v else "✗"
                disposable = " (disposable)" if result.d else ""
                print(f"{status} {email}{disposable}")
                if result.r:
                    print(f"  Reason: {result.r}")


async def error_handling_example():
    """Example: Handle various errors"""
    print("\n=== Error Handling ===")
    
    from validkit.exceptions import (
        InvalidAPIKeyError,
        RateLimitError,
        InvalidEmailError,
        ValidKitAPIError
    )
    
    async with AsyncValidKit(api_key="your_api_key") as client:
        try:
            # Invalid email format
            result = await client.verify_email("not-an-email")
        except InvalidEmailError as e:
            print(f"Invalid email: {e.email}")
        
        try:
            # API key error (using invalid key)
            bad_client = AsyncValidKit(api_key="invalid_key")
            await bad_client.verify_email("test@example.com")
        except InvalidAPIKeyError as e:
            print(f"API Key Error: {e}")
        
        try:
            # Simulate rate limit
            emails = ["test@example.com"] * 1000
            await client.verify_batch(emails)
        except RateLimitError as e:
            print(f"Rate Limited: {e}")
            print(f"Retry after: {e.retry_after} seconds")
            print(f"Limit: {e.limit}, Remaining: {e.remaining}")
        except ValidKitAPIError as e:
            print(f"API Error: {e}")


async def configuration_example():
    """Example: Custom configuration"""
    print("\n=== Custom Configuration ===")
    
    from validkit import ValidKitConfig
    
    config = ValidKitConfig(
        api_key="your_api_key",
        timeout=60,  # 60 second timeout
        max_retries=5,  # Retry up to 5 times
        rate_limit=10000,  # 10k requests per minute
        compact_format=True,  # Always use compact format
        user_agent="MyApp/1.0"
    )
    
    async with AsyncValidKit(config=config) as client:
        # This will automatically use compact format
        result = await client.verify_email("test@example.com")
        print(f"Result type: {type(result).__name__}")
        print(f"Valid: {result.v if hasattr(result, 'v') else result.valid}")


async def progress_tracking_example():
    """Example: Track progress for large batches"""
    print("\n=== Progress Tracking ===")
    
    # Generate test emails
    emails = [f"user{i}@example.com" for i in range(1000)]
    
    # Progress callback
    def progress_callback(processed, total):
        percentage = (processed / total) * 100
        print(f"Progress: {processed}/{total} ({percentage:.1f}%)")
    
    async with AsyncValidKit(api_key="your_api_key") as client:
        results = await client.verify_batch(
            emails,
            chunk_size=100,
            progress_callback=progress_callback
        )
        
        valid_count = sum(1 for r in results.values() if r.v)
        print(f"\nResults: {valid_count}/{len(emails)} valid emails")


async def streaming_example():
    """Example: Stream results as they complete"""
    print("\n=== Streaming Results ===")
    
    emails = [
        "fast@gmail.com",
        "slow@yahoo.com",
        "medium@outlook.com",
        "quick@hotmail.com",
        "turtle@aol.com"
    ]
    
    async with AsyncValidKit(api_key="your_api_key") as client:
        print("Verifying emails (results stream as they complete):")
        
        async for email, result in client.stream_verify(emails):
            status = "✓" if result.v else "✗"
            print(f"  {status} {email}")


async def trace_id_example():
    """Example: Multi-agent tracing"""
    print("\n=== Multi-Agent Tracing ===")
    
    async with AsyncValidKit(api_key="your_api_key") as client:
        # Include trace ID for debugging multi-agent workflows
        trace_id = "agent_123_task_456_subtask_789"
        
        result = await client.verify_email(
            "traced@example.com",
            trace_id=trace_id
        )
        
        print(f"Email verified with trace ID: {trace_id}")
        print(f"Result: {result}")


async def main():
    """Run all examples"""
    # Note: Replace "your_api_key" with actual API key
    
    await single_email_example()
    await batch_verification_example()
    await error_handling_example()
    await configuration_example()
    await progress_tracking_example()
    await streaming_example()
    await trace_id_example()


if __name__ == "__main__":
    asyncio.run(main())