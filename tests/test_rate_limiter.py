import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from fastapi import Request

from app.core.rate_limiter import RateLimiter, check_rate_limit
from app.config import settings


def test_rate_limiter_init():
    """Test that the rate limiter initializes correctly"""
    limiter = RateLimiter()
    assert limiter.requests == {}
    assert limiter.tokens == {}
    assert limiter.limits == {
        "chat": settings.CHAT_RATE_LIMIT_PER_MINUTE,
        "image": settings.IMAGE_RATE_LIMIT_PER_MINUTE,
        "tokens": settings.TOKEN_LIMIT_PER_MINUTE
    }


def test_rate_limiter_not_limited():
    """Test that the rate limiter allows requests when limit not reached"""
    limiter = RateLimiter()
    client_id = "test_client"
    
    is_limited, remaining = limiter.is_rate_limited(client_id, "chat")
    
    assert is_limited is False
    assert remaining["requests"] == settings.CHAT_RATE_LIMIT_PER_MINUTE - 1
    assert remaining["tokens"] == settings.TOKEN_LIMIT_PER_MINUTE
    assert client_id in limiter.requests
    assert "chat" in limiter.requests[client_id]
    assert len(limiter.requests[client_id]["chat"]) == 1


def test_rate_limiter_endpoint_limit_reached():
    """Test that the rate limiter blocks requests when endpoint limit reached"""
    limiter = RateLimiter()
    client_id = "test_client"
    
    # Add requests up to the limit
    now = datetime.utcnow()
    limiter.requests[client_id] = {
        "chat": [now for _ in range(settings.CHAT_RATE_LIMIT_PER_MINUTE)],
        "image": []
    }
    limiter.tokens[client_id] = []
    
    is_limited, remaining = limiter.is_rate_limited(client_id, "chat")
    
    assert is_limited is True
    assert remaining["requests"] == 0
    assert client_id in limiter.requests
    assert len(limiter.requests[client_id]["chat"]) == settings.CHAT_RATE_LIMIT_PER_MINUTE


def test_rate_limiter_token_limit_reached():
    """Test that the rate limiter blocks requests when token limit reached"""
    limiter = RateLimiter()
    client_id = "test_client"
    
    # Add token usage up to the limit
    now = datetime.utcnow()
    limiter.requests[client_id] = {"chat": [], "image": []}
    limiter.tokens[client_id] = [(now, settings.TOKEN_LIMIT_PER_MINUTE)]
    
    # Try to use 1 more token
    is_limited, remaining = limiter.is_rate_limited(client_id, "chat", 1)
    
    assert is_limited is True
    assert remaining["tokens"] == 0


def test_rate_limiter_cleanup_old_requests():
    """Test that the rate limiter cleans up old requests"""
    limiter = RateLimiter()
    client_id = "test_client"
    
    # Add some old requests (older than 1 minute)
    old_time = datetime.utcnow() - timedelta(minutes=2)
    limiter.requests[client_id] = {
        "chat": [old_time for _ in range(5)],
        "image": []
    }
    
    is_limited, _ = limiter.is_rate_limited(client_id, "chat")
    
    assert is_limited is False
    assert len(limiter.requests[client_id]["chat"]) == 1  # The old ones should be removed, only new one remains


@pytest.mark.asyncio
async def test_check_rate_limit_get_request():
    """Test that GET requests are not rate limited"""
    mock_request = MagicMock()
    mock_request.method = "GET"
    mock_request.client.host = "127.0.0.1"
    mock_request.url.path = "/api/chat"
    mock_request.state = MagicMock()
    
    allowed, message = await check_rate_limit(mock_request)
    
    assert allowed is True
    assert message == ""


@pytest.mark.asyncio
async def test_check_rate_limit_chat_endpoint():
    """Test rate limiting for chat endpoints"""
    with patch("app.core.rate_limiter.rate_limiter") as mock_limiter:
        mock_limiter.is_rate_limited.return_value = (False, {
            "requests": 9,
            "tokens": 90,
            "reset_in": 60
        })
        
        mock_request = MagicMock()
        mock_request.method = "POST"
        mock_request.client.host = "127.0.0.1"
        mock_request.url.path = "/api/chat"
        # When json method is called, simulate a failure
        mock_request.json.side_effect = Exception("Failed to parse JSON")
        mock_request.state = MagicMock()
        
        allowed, message = await check_rate_limit(mock_request)
        
        assert allowed is True
        assert message == ""
        # Verify it was called with the correct endpoint type and 0 tokens
        # since json parsing failed
        mock_limiter.is_rate_limited.assert_called_once_with("127.0.0.1", "chat", 0)


@pytest.mark.asyncio
async def test_check_rate_limit_image_endpoint():
    """Test rate limiting for image endpoints"""
    with patch("app.core.rate_limiter.rate_limiter") as mock_limiter:
        mock_limiter.is_rate_limited.return_value = (False, {
            "requests": 9,
            "tokens": 90,
            "reset_in": 60
        })
        
        mock_request = MagicMock()
        mock_request.method = "POST"
        mock_request.client.host = "127.0.0.1"
        mock_request.url.path = "/api/generate-image"
        # When json method is called, simulate a failure
        mock_request.json.side_effect = Exception("Failed to parse JSON")
        mock_request.state = MagicMock()
        
        allowed, message = await check_rate_limit(mock_request)
        
        assert allowed is True
        assert message == ""
        # Verify it was called with the correct endpoint type and 0 tokens
        # since json parsing failed
        mock_limiter.is_rate_limited.assert_called_once_with("127.0.0.1", "image", 0)


@pytest.mark.asyncio
async def test_check_rate_limit_with_tokens():
    """Test rate limiting with token calculation"""
    with patch("app.core.rate_limiter.rate_limiter.is_rate_limited") as mock_is_rate_limited:
        mock_is_rate_limited.return_value = (False, {
            "requests": 9,
            "tokens": 90,
            "reset_in": 60
        })
        
        mock_request = MagicMock()
        mock_request.method = "POST"
        mock_request.client.host = "127.0.0.1"
        mock_request.url.path = "/api/chat"
        # Successfully return JSON with a prompt
        mock_request.json.return_value = {"prompt": "This is a 20 character prompt"}
        mock_request.state = MagicMock()
        
        allowed, message = await check_rate_limit(mock_request)
        
        assert allowed is True
        assert message == ""
        # Verify token calculation - 20 character prompt should be 5 tokens (since 1 token ≈ 4 characters)
        mock_is_rate_limited.assert_called_once() 