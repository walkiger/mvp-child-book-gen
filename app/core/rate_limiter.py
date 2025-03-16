"""
Rate limiting functionality.
"""

from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
from fastapi import Depends, HTTPException, Request
from app.config import settings


class RateLimiter:
    def __init__(self):
        self.requests: Dict[str, Dict[str, list]] = {}  # {client_id: {endpoint: [timestamps]}}
        self.tokens: Dict[str, list] = {}  # {client_id: [(timestamp, tokens)]}
        self.limits = {
            "chat": settings.CHAT_RATE_LIMIT_PER_MINUTE,
            "image": settings.IMAGE_RATE_LIMIT_PER_MINUTE,
            "tokens": settings.TOKEN_LIMIT_PER_MINUTE
        }

    def is_rate_limited(self, client_id: str, endpoint: str, tokens: int = 0) -> Tuple[bool, Dict[str, int]]:
        """
        Check if a client is rate limited.
        Returns (is_limited, remaining_limits)
        """
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)

        # Initialize client tracking if needed
        if client_id not in self.requests:
            self.requests[client_id] = {"chat": [], "image": []}
        if client_id not in self.tokens:
            self.tokens[client_id] = []

        # Clean up old requests
        self.requests[client_id][endpoint] = [
            req_time for req_time in self.requests[client_id][endpoint]
            if req_time > minute_ago
        ]

        # Clean up old token usage
        self.tokens[client_id] = [
            (req_time, token_count) for req_time, token_count in self.tokens[client_id]
            if req_time > minute_ago
        ]

        # Check endpoint-specific rate limit
        if len(self.requests[client_id][endpoint]) >= self.limits[endpoint]:
            return True, {
                "requests": 0,
                "tokens": 0,
                "reset_in": 60 - (now - self.requests[client_id][endpoint][0]).seconds
            }

        # Calculate total tokens in the last minute
        total_tokens = sum(token_count for _, token_count in self.tokens[client_id])
        
        # Check token rate limit
        if total_tokens + tokens > self.limits["tokens"]:
            return True, {
                "requests": self.limits[endpoint] - len(self.requests[client_id][endpoint]),
                "tokens": 0,
                "reset_in": 60 - (now - self.tokens[client_id][0][0]).seconds
            }

        # Add new request and tokens
        self.requests[client_id][endpoint].append(now)
        if tokens > 0:
            self.tokens[client_id].append((now, tokens))

        # Calculate remaining limits
        remaining_requests = self.limits[endpoint] - len(self.requests[client_id][endpoint])
        remaining_tokens = self.limits["tokens"] - total_tokens

        return False, {
            "requests": remaining_requests,
            "tokens": remaining_tokens,
            "reset_in": 60
        }


# Create rate limiter instance
rate_limiter = RateLimiter()


async def check_rate_limit(request: Request) -> Tuple[bool, str]:
    """
    Check rate limits for a request.
    
    Args:
        request: The FastAPI request
    
    Returns:
        Tuple of (allowed, message)
    """
    client_id = request.client.host  # Use IP address as client identifier
    
    # Determine endpoint type (chat or image)
    endpoint_type = "chat"
    if request.url.path.endswith("/generate-image") or "image" in request.url.path:
        endpoint_type = "image"
    
    # Only apply rate limiting to POST requests
    if request.method != "POST":
        return True, ""
    
    # Estimate tokens for OpenAI API calls
    tokens = 0
    try:
        body = await request.json()
        # Rough estimation: 1 token ≈ 4 characters
        if "prompt" in body:
            tokens = len(body["prompt"]) // 4
        if "story_text" in body:
            tokens += len(body["story_text"]) // 4
    except:
        pass  # If body parsing fails, continue with 0 tokens
    
    is_limited, remaining_limits = rate_limiter.is_rate_limited(
        client_id, endpoint_type, tokens
    )
    
    if is_limited:
        return False, "Rate limit exceeded"
    
    # Add rate limit headers to response
    request.state.rate_limit_headers = {
        "X-RateLimit-Limit": str(rate_limiter.limits[endpoint_type]),
        "X-RateLimit-Remaining": str(remaining_limits["requests"]),
        "X-TokenLimit-Limit": str(rate_limiter.limits["tokens"]),
        "X-TokenLimit-Remaining": str(remaining_limits["tokens"]),
        "X-RateLimit-Reset": str(remaining_limits["reset_in"])
    }
    
    return True, "" 