# ValidKit Python SDK

[![PyPI version](https://badge.fury.io/py/validkit.svg)](https://badge.fury.io/py/validkit)
[![Python Versions](https://img.shields.io/pypi/pyversions/validkit.svg)](https://pypi.org/project/validkit/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation](https://img.shields.io/badge/docs-available-brightgreen.svg)](https://docs.validkit.com)

Async Python SDK for ValidKit Email Verification API - Built for AI Agents and high-volume applications.

## Features

- 🚀 **Fully Async**: Built on aiohttp for maximum performance
- 🤖 **AI-Agent Optimized**: Token-efficient responses and agent-friendly formats
- 📦 **Batch Processing**: Verify up to 10,000 emails in a single request
- 🔄 **Smart Retries**: Automatic retry logic with exponential backoff
- 🌊 **Connection Pooling**: Efficient connection reuse for high throughput
- 📊 **Progress Tracking**: Real-time progress updates for large batches
- 🪝 **Webhook Support**: Async webhook handling for batch results
- 🔍 **Type Safety**: Full type hints and Pydantic models

**Full API Documentation**: https://api.validkit.com/docs/openapi.json

## Installation

```bash
pip install validkit
```

## Quick Start

```python
import asyncio
from validkit import AsyncValidKit

async def main():
    # Initialize the client
    async with AsyncValidKit(api_key="your_api_key") as client:
        # Single email verification
        result = await client.verify_email("user@example.com")
        print(f"Valid: {result.valid}")
        
        # Batch verification
        emails = ["user1@example.com", "user2@example.com", "user3@example.com"]
        results = await client.verify_batch(emails)
        
        for email, result in results.items():
            print(f"{email}: {result.valid}")

asyncio.run(main())
```

## Advanced Usage

### Batch Processing with Progress

```python
async def verify_large_batch():
    async with AsyncValidKit(api_key="your_api_key") as client:
        emails = ["email{}@example.com".format(i) for i in range(10000)]
        
        # Process with progress callback
        async def progress_callback(processed, total):
            print(f"Progress: {processed}/{total} ({processed/total*100:.1f}%)")
        
        results = await client.verify_batch(
            emails,
            chunk_size=1000,
            progress_callback=progress_callback
        )
        
        valid_count = sum(1 for r in results.values() if r.valid)
        print(f"Valid emails: {valid_count}/{len(emails)}")
```

### Webhook Support

```python
# Start async batch job with webhook
job = await client.verify_batch_async(
    emails=large_email_list,
    webhook_url="https://your-app.com/webhook/validkit",
    webhook_headers={"Authorization": "Bearer your_token"}
)

print(f"Batch job started: {job.id}")
print(f"Check status at: {job.status_url}")
```

### Custom Configuration

```python
from validkit import AsyncValidKit, ValidKitConfig

config = ValidKitConfig(
    api_key="your_api_key",
    base_url="https://api.validkit.com",
    timeout=30,
    max_retries=3,
    max_connections=100,
    rate_limit=10000  # requests per minute
)

async with AsyncValidKit(config=config) as client:
    # Your code here
    pass
```

## Response Format

### Single Email Response

```python
{
    "valid": true,
    "email": "user@example.com",
    "format": {"valid": true},
    "disposable": {"valid": true, "value": false},
    "mx": {"valid": true, "records": ["mx1.example.com"]},
    "smtp": {"valid": true}
}
```

### Batch Response (Compact Format)

```python
{
    "user1@example.com": {"v": true, "d": false},
    "user2@example.com": {"v": false, "r": "invalid_format"},
    "user3@example.com": {"v": true, "d": true}
}
```

Where:
- `v`: valid (boolean)
- `d`: disposable (boolean)
- `r`: reason (string, only if invalid)

## Agent-Optimized Features

### Token-Efficient Mode

```python
# Get compact responses (80% smaller)
result = await client.verify_email(
    "user@example.com",
    format="compact"
)
```

### Multi-Agent Tracing

```python
# Include trace headers for multi-agent debugging
result = await client.verify_email(
    "user@example.com",
    trace_id="agent_123_task_456"
)
```

## Error Handling

```python
from validkit.exceptions import (
    ValidKitAPIError,
    RateLimitError,
    InvalidAPIKeyError,
    BatchSizeError
)

try:
    result = await client.verify_email("invalid-email")
except ValidKitAPIError as e:
    print(f"API Error: {e.message}")
    print(f"Error Code: {e.code}")
    print(f"Status Code: {e.status_code}")
```

## Rate Limiting

The SDK automatically handles rate limiting with smart backoff:

```python
# SDK will automatically retry with exponential backoff
results = await client.verify_batch(
    large_email_list,
    auto_retry=True  # Default: True
)
```

## Examples

Check the `examples/` directory for more detailed examples:

- `basic_usage.py` - Simple verification examples
- `batch_processing.py` - Large batch processing patterns
- `webhook_handler.py` - Webhook endpoint implementation
- `agent_integration.py` - AI agent integration patterns
- `error_handling.py` - Comprehensive error handling

## Requirements

- Python 3.8+
- aiohttp
- pydantic

## License

MIT License - see LICENSE file for details.

## Performance Tips

1. **Use batch verification** for multiple emails (up to 10,000 per request)
2. **Enable connection pooling** (default) for high-throughput applications  
3. **Set appropriate timeouts** based on your batch size
4. **Use webhooks** for large async batches to avoid long-running requests

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/ValidKit/validkit-python-sdk.git
cd validkit-python-sdk

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

## Support

- 📖 **Documentation**: https://docs.validkit.com
- 🔧 **API Reference**: https://api.validkit.com/docs/openapi.json
- 🐛 **Issues**: https://github.com/ValidKit/validkit-python-sdk/issues
- 📧 **Email**: support@validkit.com
- 💬 **Discord**: [Join our community](https://discord.gg/validkit)

---

Built with ❤️ for AI agents by [ValidKit](https://validkit.com)