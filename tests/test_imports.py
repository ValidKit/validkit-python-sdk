"""Tests that all public imports work without crashing.

This is the test that would have caught the original ImportError crash
from pydantic's EmailStr requiring the email-validator package.
"""


def test_import_async_validkit():
    from validkit import AsyncValidKit
    assert AsyncValidKit is not None


def test_import_config():
    from validkit import ValidKitConfig
    assert ValidKitConfig is not None


def test_import_models():
    from validkit import (
        EmailVerificationResult,
        BatchVerificationResult,
        BatchJob,
        CompactResult,
        FormatCheck,
        DisposableCheck,
        MXCheck,
        SMTPCheck,
    )
    assert EmailVerificationResult is not None
    assert BatchVerificationResult is not None
    assert BatchJob is not None
    assert CompactResult is not None


def test_import_exceptions():
    from validkit import (
        ValidKitError,
        ValidKitAPIError,
        InvalidAPIKeyError,
        RateLimitError,
        BatchSizeError,
        TimeoutError,
        ConnectionError,
    )
    assert ValidKitError is not None
    assert RateLimitError is not None


def test_version():
    from validkit import __version__
    assert __version__ == "1.1.2"


def test_version_single_source_of_truth():
    """All version references must come from _version.py."""
    from validkit._version import __version__ as source_version
    from validkit import __version__ as init_version
    from validkit.config import ValidKitConfig

    config = ValidKitConfig(api_key="test")

    assert init_version == source_version, (
        f"__init__.__version__ ({init_version}) != _version.__version__ ({source_version})"
    )
    assert config.headers["X-SDK-Version"] == source_version
    assert source_version in config.user_agent


def test_no_email_validator_required():
    """Verify the SDK works without the email-validator package.

    This is the core regression test for the original #2254 crash.
    If EmailStr were still used, this import would fail on systems
    without email-validator installed.
    """
    import importlib
    # Force re-import to catch import-time errors
    import validkit.models
    importlib.reload(validkit.models)
