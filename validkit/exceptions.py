"""Exception classes for ValidKit SDK"""

from typing import Optional, Dict, Any


class ValidKitError(Exception):
    """Base exception for all ValidKit errors"""
    pass


class ValidKitAPIError(ValidKitError):
    """API-related errors"""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details or {}
    
    def __str__(self) -> str:
        parts = [self.message]
        if self.status_code:
            parts.append(f"(Status: {self.status_code})")
        if self.code:
            parts.append(f"[Code: {self.code}]")
        return " ".join(parts)


class InvalidAPIKeyError(ValidKitAPIError):
    """Invalid API key error"""
    
    def __init__(self, message: str = "Invalid API key"):
        super().__init__(message, status_code=401, code="INVALID_API_KEY")


class RateLimitError(ValidKitAPIError):
    """Rate limit exceeded error"""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        limit: Optional[int] = None,
        remaining: Optional[int] = None,
        reset: Optional[int] = None
    ):
        details = {}
        if retry_after is not None:
            details["retry_after"] = retry_after
        if limit is not None:
            details["limit"] = limit
        if remaining is not None:
            details["remaining"] = remaining
        if reset is not None:
            details["reset"] = reset
            
        super().__init__(message, status_code=429, code="RATE_LIMIT_EXCEEDED", details=details)
        self.retry_after = retry_after
        self.limit = limit
        self.remaining = remaining
        self.reset = reset


class BatchSizeError(ValidKitAPIError):
    """Batch size exceeded error"""
    
    def __init__(self, size: int, max_size: int):
        message = f"Batch size {size} exceeds maximum allowed size {max_size}"
        super().__init__(message, status_code=400, code="BATCH_SIZE_EXCEEDED")
        self.size = size
        self.max_size = max_size


class TimeoutError(ValidKitError):
    """Request timeout error"""
    pass


class ConnectionError(ValidKitError):
    """Connection-related error"""
    pass


class InvalidEmailError(ValidKitAPIError):
    """Invalid email format error"""
    
    def __init__(self, email: str):
        message = f"Invalid email format: {email}"
        super().__init__(message, status_code=400, code="INVALID_EMAIL")
        self.email = email


class WebhookError(ValidKitError):
    """Webhook-related error"""
    pass


class ConfigurationError(ValidKitError):
    """Configuration-related error"""
    pass