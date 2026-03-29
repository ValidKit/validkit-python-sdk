# ValidKit Python SDK

[![PyPI version](https://badge.fury.io/py/validkit.svg)](https://pypi.org/project/validkit/)
[![Python Versions](https://img.shields.io/pypi/pyversions/validkit.svg)](https://pypi.org/project/validkit/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Email validation for signup flows -- block junk without blocking `test+staging@example.com`. Async Python client with batch support up to 10K emails, automatic retries, and Pydantic models.

## Installation

```bash
pip install validkit
```

Requires Python 3.8+.

## Quick Start

```python
import asyncio
from validkit import AsyncValidKit

async def main():
    async with AsyncValidKit(api_key="your_api_key") as client:
        # Single email
        result = await client.verify_email("user@example.com")
        print(result.valid)  # True

        # Batch -- compact format by default
        results = await client.verify_batch([
            "alice@company.com",
            "bob@tempmail.com",
            "not-an-email",
        ])
        for email, r in results.items():
            print(f"{email}: valid={r.v}, disposable={r.d}")

asyncio.run(main())
```

## Features

- **Async-native** -- aiohttp with connection pooling (100 connections default)
- **Batch verification** -- up to 10,000 emails per call, chunked automatically
- **Developer Pattern Intelligence** -- understands `test@`, `+addressing`, disposable domains
- **Compact format** -- token-efficient responses (`v`, `d`, `r` fields) enabled by default
- **Streaming** -- `async for` results as they complete
- **Webhook delivery** -- fire-and-forget async batch jobs with callback
- **Automatic retries** -- exponential backoff, 3 retries default
- **Type-safe** -- Pydantic v2 models with full type hints

## Advanced Usage

### Custom configuration

```python
from validkit import AsyncValidKit, ValidKitConfig

config = ValidKitConfig(
    api_key="your_api_key",
    timeout=30,           # seconds
    max_retries=3,        # retry count
    max_connections=100,   # connection pool size
    rate_limit=10000,     # requests/min (None = unlimited)
    compact_format=True,  # smaller payloads
)

async with AsyncValidKit(config=config) as client:
    result = await client.verify_email("user@example.com")
```

### Batch with progress tracking

```python
def on_progress(processed, total):
    print(f"{processed}/{total} ({processed / total * 100:.1f}%)")

results = await client.verify_batch(
    emails,
    chunk_size=1000,
    progress_callback=on_progress,
)
```

### Async batch with webhook

```python
job = await client.verify_batch_async(
    emails=large_list,
    webhook_url="https://your-app.com/webhooks/validkit",
    webhook_headers={"Authorization": "Bearer token"},
)

# Poll until complete, or wait for webhook
job = await client.get_batch_status(job.id)
results = await client.get_batch_results(job.id)

# Cancel if needed
await client.cancel_batch(job.id)
```

### Streaming

```python
async for email, result in client.stream_verify(emails, batch_size=100):
    print(f"{email}: valid={result.v}")
```

### Trace IDs

Attach a trace ID for cross-service debugging:

```python
result = await client.verify_email("user@example.com", trace_id="req_abc123")
```

## Error Handling

```python
from validkit.exceptions import (
    ValidKitError,       # base -- catches everything
    ValidKitAPIError,    # API errors (4xx, 5xx)
    InvalidAPIKeyError,  # 401
    RateLimitError,      # 429, includes retry_after
    BatchSizeError,      # batch exceeds 10K
    TimeoutError,        # request timeout (inherits ValidKitError, not API)
    ConnectionError,     # network failure (inherits ValidKitError, not API)
)

try:
    result = await client.verify_email("user@example.com")
except RateLimitError as e:
    print(e.retry_after)  # seconds until retry
except InvalidAPIKeyError:
    print("Check your API key")
except ValidKitAPIError as e:
    print(e.message, e.status_code, e.code)
except ValidKitError as e:
    # Catches TimeoutError, ConnectionError, and any other non-API errors
    print(f"SDK error: {e}")
```

The SDK retries automatically on rate limits and transient errors (up to `max_retries`). Catch exceptions only if you need custom handling.

## Compact Response Format

Default format. Smaller payloads, same information:

| Field | Type | Meaning |
|-------|------|---------|
| `v` | `bool` | Email is valid |
| `d` | `bool \| None` | Domain is disposable (None if not checked) |
| `r` | `str \| None` | Reason (present only when invalid) |

```python
# Compact (default)
r = await client.verify_email("bad@example.com")
print(r.v, r.d, r.r)  # False, False, "invalid_format"

# Full format -- use when you need MX records, SMTP details
from validkit.models import ResponseFormat
full = await client.verify_email("user@example.com", format=ResponseFormat.FULL)
if full.mx:
    print(full.mx.records)  # ["mx1.example.com"]
```

## Examples

See [`examples/`](examples/):

- [`basic_usage.py`](examples/basic_usage.py) -- single verification, batch, streaming, configuration
- [`batch_processing.py`](examples/batch_processing.py) -- large batches, CSV processing, webhook jobs, domain analysis

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Support

[Docs](https://docs.validkit.com) -- [GitHub Issues](https://github.com/ValidKit/validkit-python-sdk/issues) -- support@validkit.com

## License

MIT -- see [LICENSE](LICENSE).