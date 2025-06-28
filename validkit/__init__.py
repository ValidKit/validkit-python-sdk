"""
ValidKit Python SDK
Async email verification for AI agents and high-volume applications
"""

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

__version__ = "1.0.1"
__author__ = "ValidKit"
__email__ = "support@validkit.com"

__all__ = [
    # Client
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