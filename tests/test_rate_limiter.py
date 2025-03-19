"""
Tests for the rate limiter functionality and error handling.
"""
import pytest
import time
from unittest.mock import MagicMock, patch
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, UTC

from app.core.rate_limiter import RateLimiter
from app.config import get_settings
from app.core.errors.base import ErrorContext, ErrorSeverity, RetryConfig
from app.core.errors.rate_limiter import (
    RateLimitError,
    RateLimitExceededError,
    RateLimitConfigError
)


@pytest.fixture
def error_context():
    """Create a test error context for rate limiter operations."""
    return ErrorContext(
        source="test.rate_limiter",
        severity=ErrorSeverity.ERROR,
        timestamp=datetime.now(UTC),
        error_id="test-rate-limiter-id",
        additional_data={"operation": "test"}
    )


def test_rate_limiter_init(error_context):
    """Test that the rate limiter initializes correctly"""
    try:
        limiter = RateLimiter()
        assert limiter._store == {}
        assert limiter._test_limits is None
        assert "default" in limiter.limits
        assert "chat" in limiter.limits
        assert "image" in limiter.limits
        assert "token" in limiter.limits
    except Exception as e:
        error_context.additional_data.update({
            "operation": "init_rate_limiter"
        })
        raise RateLimitError("Failed to initialize rate limiter", error_context) from e


def test_rate_limiter_test_limits(error_context):
    """Test setting and resetting test limits"""
    try:
        limiter = RateLimiter()
        test_limits = {
            "default": 5,
            "chat": 3,
            "image": 2,
            "token": 1
        }
        
        # Set test limits
        limiter.set_test_limits(test_limits)
        assert limiter.limits == test_limits
        
        # Reset limits
        limiter.reset_limits()
        assert limiter.limits != test_limits
        assert limiter._test_limits is None
    except Exception as e:
        error_context.additional_data.update({
            "operation": "test_limits",
            "test_limits": test_limits
        })
        raise RateLimitConfigError("Failed to set/reset test limits", error_context) from e


def test_rate_limiter_window_calculation(error_context):
    """Test window start time calculation"""
    try:
        limiter = RateLimiter()
        now = 1000.0  # Use a simple timestamp for testing
        
        window_start = limiter._get_window_start(now)
        assert window_start == 960.0  # Should round down to nearest minute
    except Exception as e:
        error_context.additional_data.update({
            "operation": "window_calculation",
            "timestamp": now
        })
        raise RateLimitError("Failed to calculate window start time", error_context) from e


def test_rate_limiter_key_generation(error_context):
    """Test rate limit key generation"""
    try:
        limiter = RateLimiter()
        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {}
        mock_request.state = MagicMock()
        mock_request.state.user_id = None  # This will make it use "anonymous"
        
        key = limiter._get_key(mock_request, "chat")
        assert "chat:127.0.0.1:anonymous" in key

        # Test with forwarded IP
        mock_request.headers = {"X-Forwarded-For": "10.0.0.1"}
        key = limiter._get_key(mock_request, "chat")
        assert "chat:10.0.0.1:anonymous" in key

        # Test with user ID
        mock_request.state.user_id = "123"
        key = limiter._get_key(mock_request, "chat")
        assert "chat:10.0.0.1:123" in key
    except Exception as e:
        error_context.additional_data.update({
            "operation": "key_generation",
            "ip": mock_request.client.host,
            "user_id": getattr(mock_request.state, "user_id", None)
        })
        raise RateLimitError("Failed to generate rate limit key", error_context) from e


def test_rate_limiter_check_limit_success(error_context):
    """Test successful rate limit check"""
    try:
        limiter = RateLimiter()
        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {}
        mock_request.state = MagicMock()
        mock_request.state.user_id = None
        
        # Should not raise an exception
        limiter.check_rate_limit(mock_request)
        
        # Check that the store was updated
        key = limiter._get_key(mock_request, "default")
        assert key in limiter._store
        assert limiter._store[key]["count"] == 1
    except Exception as e:
        error_context.additional_data.update({
            "operation": "check_limit",
            "ip": mock_request.client.host,
            "limit_type": "default"
        })
        raise RateLimitError("Failed to check rate limit", error_context) from e


def test_rate_limiter_check_limit_exceeded(error_context):
    """Test rate limit exceeded"""
    try:
        limiter = RateLimiter()
        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {}
        mock_request.state = MagicMock()
        mock_request.state.user_id = None
        
        # Set a low test limit
        limiter.set_test_limits({"default": 2})
        
        # Make requests up to the limit
        limiter.check_rate_limit(mock_request)
        limiter.check_rate_limit(mock_request)
        
        # Next request should fail
        with pytest.raises(RateLimitExceededError) as exc_info:
            try:
                limiter.check_rate_limit(mock_request)
            except HTTPException as e:
                error_context.additional_data.update({
                    "limit_type": "default",
                    "current_count": 2,
                    "max_limit": 2,
                    "retry_after": e.headers.get("Retry-After")
                })
                raise RateLimitExceededError("Rate limit exceeded", error_context) from e
        
        assert exc_info.value.error_code == "RATE-LIM-001"
        assert "Rate limit exceeded" in str(exc_info.value)
        assert exc_info.value.error_context.source == "test.rate_limiter"
        assert exc_info.value.error_context.severity == ErrorSeverity.ERROR
        assert "retry_after" in exc_info.value.error_context.additional_data
    except Exception as e:
        error_context.additional_data.update({
            "operation": "check_limit_exceeded",
            "ip": mock_request.client.host,
            "limit_type": "default"
        })
        raise RateLimitError("Failed to test rate limit exceeded", error_context) from e


def test_rate_limiter_window_reset(error_context):
    """Test that rate limit window resets properly"""
    try:
        limiter = RateLimiter()
        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {}
        mock_request.state = MagicMock()
        mock_request.state.user_id = None
        
        # Set up an expired window
        key = limiter._get_key(mock_request, "default")
        old_window = time.time() - 120  # 2 minutes ago
        limiter._store[key] = {"start": old_window, "count": 999}
        
        # Should not raise an exception as window should reset
        limiter.check_rate_limit(mock_request)
        
        # Check that the store was updated with a new window
        assert limiter._store[key]["count"] == 1
        assert limiter._store[key]["start"] > old_window
    except Exception as e:
        error_context.additional_data.update({
            "operation": "window_reset",
            "ip": mock_request.client.host,
            "old_window": old_window
        })
        raise RateLimitError("Failed to test window reset", error_context) from e


def test_get_remaining_requests(error_context):
    """Test getting remaining request count"""
    try:
        limiter = RateLimiter()
        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {}
        mock_request.state = MagicMock()
        mock_request.state.user_id = None
        
        # Set test limits including default
        limiter.set_test_limits({
            "default": 10,
            "chat": 5
        })
        
        # Make some requests
        for _ in range(3):
            limiter.check_rate_limit(mock_request, "chat")
        
        # Check remaining
        remaining = limiter.get_remaining(mock_request, "chat")
        assert remaining == 2  # 5 limit - 3 used = 2 remaining
    except Exception as e:
        error_context.additional_data.update({
            "operation": "get_remaining",
            "ip": mock_request.client.host,
            "limit_type": "chat"
        })
        raise RateLimitError("Failed to get remaining requests", error_context) from e 