"""
Rate limiting functionality for API endpoints.
"""

import time
from datetime import datetime
from typing import Dict, Optional
from fastapi import Request
from app.config import get_settings
from .errors.rate_limit import (
    QuotaExceededError,
    ConcurrencyLimitError,
    BurstLimitError,
    CostLimitError
)
from .errors.base import ErrorContext, ErrorSeverity
from .ai_utils import check_rate_limits, update_rate_metrics

# Set up logger
import logging
logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter implementation using a simple in-memory store."""
    
    def __init__(self):
        """Initialize rate limiter with default limits."""
        self._store: Dict[str, Dict[str, float]] = {}
        self._settings = None
        self._test_limits: Optional[Dict[str, int]] = None
        self._default_limits = {
            "default": 60,  # Default API limit
            "openai": {
                "chat": 5,     # OpenAI chat completions limit
                "image": 3,    # OpenAI image generation limit
                "token": 20000 # OpenAI token limit
            }
        }
        
    @property
    def settings(self):
        """Get settings lazily."""
        context = ErrorContext(
            source="rate_limiter.settings",
            severity=ErrorSeverity.ERROR
        )
        
        if self._settings is None:
            try:
                self._settings = get_settings()
            except ValueError as e:
                logger.warning("Settings validation failed, using default limits")
                # If settings validation fails, use default limits
                return type('Settings', (), {
                    'chat_rate_limit_per_minute': self._default_limits["openai"]["chat"],
                    'image_rate_limit_per_minute': self._default_limits["openai"]["image"],
                    'token_limit_per_minute': self._default_limits["openai"]["token"]
                })()
        return self._settings
        
    @property
    def limits(self) -> Dict[str, int]:
        """Get rate limits from settings or test configuration."""
        if self._test_limits is not None:
            return self._test_limits
        try:
            return {
                "default": self._default_limits["default"],
                "openai": {
                    "chat": self.settings.chat_rate_limit_per_minute,
                    "image": self.settings.image_rate_limit_per_minute,
                    "token": self.settings.token_limit_per_minute
                }
            }
        except (AttributeError, ValueError):
            logger.warning("Failed to get limits from settings, using defaults")
            return self._default_limits.copy()
    
    def set_test_limits(self, limits: Dict[str, int]):
        """Set test-specific rate limits. For testing only."""
        self._test_limits = limits.copy()  # Make a copy to prevent external modification

    def reset_limits(self):
        """Reset to default limits. For testing only."""
        self._test_limits = None
        self._store.clear()  # Clear the store when resetting limits
    
    def _get_window_start(self, now: float) -> float:
        """Get the start of the current minute window."""
        return now - (now % 60)
    
    def _get_key(self, request: Request, limit_type: str) -> str:
        """Generate a unique key for the request."""
        # Get client IP - handle proxy forwarding
        client_ip = request.client.host
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
            
        # Get user ID from token if available
        user_id = getattr(request.state, "user_id", None)
        user_id = str(user_id) if user_id is not None else "anonymous"
            
        return f"{limit_type}:{client_ip}:{user_id}"
    
    def check_rate_limit(self, request: Request, limit_type: str = "default") -> None:
        """
        Check if the request exceeds rate limits.
        
        Args:
            request: FastAPI request object
            limit_type: Type of rate limit to check
            
        Raises:
            QuotaExceededError: When rate limit is exceeded
        """
        # For OpenAI endpoints, use the OpenAI-specific rate limiter
        if limit_type.startswith("openai_"):
            check_rate_limits()
            return

        context = ErrorContext(
            source="rate_limiter.check_rate_limit",
            severity=ErrorSeverity.WARNING
        )
        
        now = time.time()
        window_start = self._get_window_start(now)
        key = self._get_key(request, limit_type)
        
        # Get limit for the type
        limit = self.limits.get(limit_type, self.limits["default"])
        if isinstance(limit, dict):
            limit = limit.get("default", self._default_limits["default"])
        
        # Get or initialize window data
        window = self._store.get(key)
        
        # Reset window if it's expired or doesn't exist
        if window is None or window["start"] < window_start:
            window = {"start": window_start, "count": 0}
            self._store[key] = window
        
        # Check limit
        if window["count"] >= limit:
            retry_after = int(window["start"] + 60 - now)
            reset_time = datetime.fromtimestamp(window["start"] + 60)
            
            # Add rate limit headers
            request.state.rate_limit_headers = {
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(window["start"] + 60))
            }
            
            raise QuotaExceededError(
                message=f"Rate limit exceeded for {limit_type}",
                limit_type=limit_type,
                current_usage=window["count"],
                limit=limit,
                reset_time=reset_time,
                context=context,
                details={
                    "retry_after": retry_after,
                    "window_start": window["start"],
                    "window_end": window["start"] + 60
                }
            )
        
        # Update window
        window["count"] += 1
        remaining = limit - window["count"]
        
        # Add rate limit headers
        request.state.rate_limit_headers = {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(int(window["start"] + 60))
        }

    def get_remaining(self, request: Request, limit_type: str = "default") -> int:
        """Get remaining requests in the current window."""
        now = time.time()
        window_start = self._get_window_start(now)
        key = self._get_key(request, limit_type)
        
        # Get limit for the type
        limit = self.limits.get(limit_type, self.limits["default"])
        if isinstance(limit, dict):
            limit = limit.get("default", self._default_limits["default"])
        
        # Get window data
        window = self._store.get(key)
        
        # If no window or expired window, return full limit
        if window is None or window["start"] < window_start:
            return limit
            
        return max(0, limit - window["count"])

    def clear_store(self):
        """Clear the rate limit store. For testing only."""
        self._store.clear()


# Global rate limiter instance
rate_limiter = RateLimiter() 