"""Tests for Pydantic model deserialization.

Verifies that SDK models can deserialize responses from the ValidKit API
without requiring email-validator or any extra dependencies.
"""

import pytest
from datetime import datetime
from validkit.models import (
    EmailVerificationResult,
    BatchVerificationResult,
    BatchJob,
    CompactResult,
    FormatCheck,
    DisposableCheck,
    MXCheck,
    SMTPCheck,
    BatchJobStatus,
    WebhookPayload,
)


class TestEmailVerificationResult:
    def test_minimal(self):
        r = EmailVerificationResult(success=True, email="test@example.com", valid=True)
        assert r.success is True
        assert r.email == "test@example.com"
        assert r.valid is True

    def test_email_is_plain_str(self):
        """Email field must be plain str, not EmailStr (which requires email-validator)."""
        r = EmailVerificationResult(success=True, email="test@example.com", valid=True)
        assert isinstance(r.email, str)

    def test_full_response(self):
        r = EmailVerificationResult(
            success=True,
            email="user@gmail.com",
            valid=True,
            format=FormatCheck(valid=True),
            disposable=DisposableCheck(valid=True, value=False),
            mx=MXCheck(valid=True, records=["mx1.gmail.com", "mx2.gmail.com"]),
            smtp=SMTPCheck(valid=True, code=250, message="OK"),
            processing_time_ms=42,
            trace_id="trace-abc-123",
        )
        assert r.format.valid is True
        assert r.disposable.value is False
        assert len(r.mx.records) == 2
        assert r.smtp.code == 250
        assert r.processing_time_ms == 42

    def test_optional_fields_default_none(self):
        r = EmailVerificationResult(success=False, email="bad@test.com", valid=False)
        assert r.format is None
        assert r.disposable is None
        assert r.mx is None
        assert r.smtp is None
        assert r.processing_time_ms is None


class TestCompactResult:
    def test_valid_email(self):
        r = CompactResult(v=True)
        assert r.v is True
        assert r.d is None
        assert r.r is None

    def test_invalid_email_with_reason(self):
        r = CompactResult(v=False, r="invalid_format")
        assert r.v is False
        assert r.r == "invalid_format"

    def test_disposable_flag(self):
        r = CompactResult(v=True, d=True)
        assert r.d is True


class TestBatchVerificationResult:
    def test_minimal(self):
        r = BatchVerificationResult(
            success=True,
            total=2,
            valid=1,
            invalid=1,
            results={
                "good@test.com": CompactResult(v=True),
                "bad@test.com": CompactResult(v=False, r="invalid"),
            },
        )
        assert r.total == 2
        assert r.valid == 1
        assert len(r.results) == 2

    def test_with_metadata(self):
        r = BatchVerificationResult(
            success=True,
            total=1,
            valid=1,
            invalid=0,
            results={"a@b.com": CompactResult(v=True)},
            batch_id="batch-123",
            processing_time_ms=500,
            rate_limit=1000,
            rate_remaining=999,
        )
        assert r.batch_id == "batch-123"
        assert r.rate_remaining == 999


class TestBatchJob:
    def test_minimal(self):
        now = datetime.now()
        job = BatchJob(
            id="job-123",
            status=BatchJobStatus.PENDING,
            total_emails=100,
            created_at=now,
            updated_at=now,
        )
        assert job.id == "job-123"
        assert job.status == BatchJobStatus.PENDING

    def test_progress_percentage(self):
        now = datetime.now()
        job = BatchJob(
            id="job-1",
            status=BatchJobStatus.PROCESSING,
            total_emails=200,
            processed=100,
            created_at=now,
            updated_at=now,
        )
        assert job.progress_percentage == 50.0

    def test_progress_percentage_zero_total(self):
        now = datetime.now()
        job = BatchJob(
            id="job-1",
            status=BatchJobStatus.PENDING,
            total_emails=0,
            created_at=now,
            updated_at=now,
        )
        assert job.progress_percentage == 0.0

    def test_is_complete(self):
        now = datetime.now()
        for status in [BatchJobStatus.COMPLETED, BatchJobStatus.FAILED, BatchJobStatus.CANCELLED]:
            job = BatchJob(
                id="job-1",
                status=status,
                total_emails=10,
                created_at=now,
                updated_at=now,
            )
            assert job.is_complete is True

    def test_is_not_complete(self):
        now = datetime.now()
        for status in [BatchJobStatus.PENDING, BatchJobStatus.PROCESSING]:
            job = BatchJob(
                id="job-1",
                status=status,
                total_emails=10,
                created_at=now,
                updated_at=now,
            )
            assert job.is_complete is False
