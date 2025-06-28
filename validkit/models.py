"""Data models for ValidKit SDK"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, EmailStr, validator


class ResponseFormat(str, Enum):
    """Response format options"""
    FULL = "full"
    COMPACT = "compact"


class VerificationStatus(str, Enum):
    """Verification status"""
    VALID = "valid"
    INVALID = "invalid"
    UNKNOWN = "unknown"


class DisposableProvider(str, Enum):
    """Known disposable email providers"""
    TEMPMAIL = "tempmail"
    GUERRILLA = "guerrilla"
    MAILINATOR = "mailinator"
    YOPMAIL = "yopmail"
    OTHER = "other"


class FormatCheck(BaseModel):
    """Email format validation result"""
    valid: bool
    reason: Optional[str] = None


class DisposableCheck(BaseModel):
    """Disposable email check result"""
    valid: bool
    value: bool = Field(description="True if email is disposable")
    provider: Optional[DisposableProvider] = None


class MXCheck(BaseModel):
    """MX record check result"""
    valid: bool
    records: Optional[List[str]] = None
    priority: Optional[List[int]] = None


class SMTPCheck(BaseModel):
    """SMTP validation result"""
    valid: bool
    code: Optional[int] = None
    message: Optional[str] = None


class EmailVerificationResult(BaseModel):
    """Full email verification result"""
    success: bool
    email: EmailStr
    valid: bool
    
    # Detailed checks
    format: Optional[FormatCheck] = None
    disposable: Optional[DisposableCheck] = None
    mx: Optional[MXCheck] = None
    smtp: Optional[SMTPCheck] = None
    
    # Additional metadata
    processing_time_ms: Optional[int] = None
    timestamp: Optional[datetime] = None
    trace_id: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CompactResult(BaseModel):
    """Compact verification result for token efficiency"""
    v: bool = Field(description="Valid")
    d: Optional[bool] = Field(None, description="Disposable")
    r: Optional[str] = Field(None, description="Reason if invalid")
    
    @validator('r')
    def reason_only_if_invalid(cls, v, values):
        if values.get('v') and v:
            return None
        return v


class BatchVerificationResult(BaseModel):
    """Batch verification response"""
    success: bool
    total: int
    valid: int
    invalid: int
    results: Dict[str, Union[EmailVerificationResult, CompactResult]]
    
    # Batch metadata
    batch_id: Optional[str] = None
    processing_time_ms: Optional[int] = None
    timestamp: Optional[datetime] = None
    
    # Rate limit info
    rate_limit: Optional[int] = None
    rate_remaining: Optional[int] = None
    rate_reset: Optional[int] = None


class BatchJobStatus(str, Enum):
    """Batch job status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BatchJob(BaseModel):
    """Async batch job information"""
    id: str
    status: BatchJobStatus
    total_emails: int
    processed: int = 0
    valid: int = 0
    invalid: int = 0
    
    # URLs
    status_url: Optional[str] = None
    results_url: Optional[str] = None
    cancel_url: Optional[str] = None
    
    # Webhook info
    webhook_url: Optional[str] = None
    webhook_status: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    # Error info
    error: Optional[str] = None
    failed_emails: Optional[List[str]] = None
    
    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage"""
        if self.total_emails == 0:
            return 0.0
        return (self.processed / self.total_emails) * 100
    
    @property
    def is_complete(self) -> bool:
        """Check if job is complete"""
        return self.status in [BatchJobStatus.COMPLETED, BatchJobStatus.FAILED, BatchJobStatus.CANCELLED]


class WebhookPayload(BaseModel):
    """Webhook payload for batch results"""
    event: str = "batch.completed"
    batch_id: str
    status: BatchJobStatus
    results: BatchVerificationResult
    timestamp: datetime
    
    # Optional signature for verification
    signature: Optional[str] = None