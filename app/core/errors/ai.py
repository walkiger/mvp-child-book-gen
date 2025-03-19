"""
AI Error Handling

This module defines AI-specific errors extending the base error system.
"""

from typing import Optional, Dict, Any, List

from .base import BaseError, ErrorContext, ErrorSeverity


class AIError(BaseError):
    """Base class for all AI-related errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        http_status_code: int = 500,
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None
    ):
        if not error_code.startswith('AI-'):
            error_code = f"AI-{error_code}"
        super().__init__(
            message,
            error_code,
            http_status_code,
            context,
            details,
            suggestions
        )
        self.set_severity(ErrorSeverity.ERROR)


class AIClientError(AIError):
    """Error raised when there are issues with the AI client."""
    
    def __init__(
        self,
        message: str,
        client_name: str = "OpenAI",
        operation: str = "API call",
        error_code: str = "AI-CLIENT-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            "client_name": client_name,
            "operation": operation
        })
        
        super().__init__(
            message,
            error_code,
            http_status_code=500,
            context=context,
            details=details,
            suggestions=[
                f"Check {client_name} API credentials",
                "Verify API endpoint availability",
                "Check request format and parameters",
                "Review API documentation"
            ]
        )


class AIResponseError(AIError):
    """Error raised when there are issues with AI response processing."""
    
    def __init__(
        self,
        message: str,
        response_type: str,
        error_code: str = "AI-RESP-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            "response_type": response_type
        })
        
        super().__init__(
            message,
            error_code,
            http_status_code=500,
            context=context,
            details=details,
            suggestions=[
                "Check response format",
                "Verify model output structure",
                "Review prompt engineering"
            ]
        )


class AIRateLimitError(AIError):
    """Error raised when AI API rate limits are exceeded."""
    
    def __init__(
        self,
        message: str,
        limit_type: str,
        error_code: str = "AI-RATE-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            "limit_type": limit_type
        })
        
        super().__init__(
            message,
            error_code,
            http_status_code=429,
            context=context,
            details=details,
            suggestions=[
                "Implement request throttling",
                "Check rate limit quotas",
                "Consider batch processing",
                "Optimize API usage"
            ]
        ) 