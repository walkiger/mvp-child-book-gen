"""
Rate Limiting Error Handling

This module defines rate limiting-specific errors extending the base error system.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List

from .base import BaseError, ErrorContext, ErrorSeverity


class RateLimitError(BaseError):
    """Base class for all rate limiting-related errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        http_status_code: int = 429,
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None
    ):
        if not error_code.startswith('RATE-'):
            error_code = f"RATE-{error_code}"
        super().__init__(
            message,
            error_code,
            http_status_code,
            context,
            details,
            suggestions
        )


class QuotaExceededError(RateLimitError):
    """Rate limit quota exceeded errors."""
    
    def __init__(
        self,
        message: str,
        limit_type: str,
        current_usage: int,
        limit: int,
        reset_time: datetime,
        error_code: str = "RATE-QUOTA-EXC-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            'limit_type': limit_type,
            'current_usage': current_usage,
            'limit': limit,
            'reset_time': reset_time.isoformat()
        })
        
        super().__init__(
            message,
            error_code,
            http_status_code=429,
            context=context,
            details=details,
            suggestions=[
                f"Wait until {reset_time.isoformat()}",
                "Reduce request frequency",
                "Check quota limits"
            ]
        )
        self.set_severity(ErrorSeverity.WARNING)


class ConcurrencyLimitError(RateLimitError):
    """Concurrent requests limit errors."""
    
    def __init__(
        self,
        message: str,
        max_concurrent: int,
        current_concurrent: int,
        error_code: str = "RATE-CONC-LIM-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            'max_concurrent': max_concurrent,
            'current_concurrent': current_concurrent
        })
        
        super().__init__(
            message,
            error_code,
            http_status_code=429,
            context=context,
            details=details,
            suggestions=[
                "Wait for other requests to complete",
                "Reduce concurrent requests",
                f"Maximum concurrent requests: {max_concurrent}"
            ]
        )
        self.set_severity(ErrorSeverity.WARNING)


class BurstLimitError(RateLimitError):
    """Request burst limit errors."""
    
    def __init__(
        self,
        message: str,
        burst_limit: int,
        current_burst: int,
        window_seconds: int,
        error_code: str = "RATE-BURST-LIM-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            'burst_limit': burst_limit,
            'current_burst': current_burst,
            'window_seconds': window_seconds
        })
        
        super().__init__(
            message,
            error_code,
            http_status_code=429,
            context=context,
            details=details,
            suggestions=[
                f"Maximum {burst_limit} requests per {window_seconds} seconds",
                "Implement request throttling",
                "Add delay between requests"
            ]
        )
        self.set_severity(ErrorSeverity.WARNING)


class CostLimitError(RateLimitError):
    """Cost-based rate limit errors."""
    
    def __init__(
        self,
        message: str,
        cost_limit: float,
        current_cost: float,
        reset_time: datetime,
        error_code: str = "RATE-COST-LIM-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            'cost_limit': cost_limit,
            'current_cost': current_cost,
            'reset_time': reset_time.isoformat()
        })
        
        super().__init__(
            message,
            error_code,
            http_status_code=429,
            context=context,
            details=details,
            suggestions=[
                f"Wait until {reset_time.isoformat()}",
                "Reduce resource usage",
                "Check cost allocation"
            ]
        )
        self.set_severity(ErrorSeverity.WARNING) 