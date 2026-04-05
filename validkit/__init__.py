"""
ValidKit Python SDK
Email validation for signup flows.
"""

from .sync_client import ValidKit
from .client import AsyncValidKit
from .config import ValidKitConfig
from .models import (
    EmailVerificationResult,
    BatchVerificationResult,
    BatchJob,
    CompactResult,
    FormatCheck,
    DisposableCheck,
    MXCheck,
    SMTPCheck
)
from .exceptions import (
    ValidKitError,
    ValidKitAPIError,
    InvalidAPIKeyError,
    RateLimitError,
    BatchSizeError,
    TimeoutError,
    ConnectionError
)

from validkit._version import __version__  # noqa: E402
__author__ = "ValidKit"
__email__ = "developers@validkit.com"

__all__ = [
    # Client
    "ValidKit",
    "AsyncValidKit",
    "ValidKitConfig",
    
    # Models
    "EmailVerificationResult",
    "BatchVerificationResult",
    "BatchJob",
    "CompactResult",
    "FormatCheck",
    "DisposableCheck",
    "MXCheck",
    "SMTPCheck",
    
    # Exceptions
    "ValidKitError",
    "ValidKitAPIError",
    "InvalidAPIKeyError",
    "RateLimitError",
    "BatchSizeError",
    "TimeoutError",
    "ConnectionError",
]