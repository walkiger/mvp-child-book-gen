"""
API Error Handling

This module defines API-specific errors extending the base error system.
"""

import functools
from typing import Optional, Dict, Any, List, Callable
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from .base import BaseError, ErrorContext, ErrorSeverity

def with_api_error_handling(func: Callable):
    """Decorator to handle API errors and convert them to appropriate HTTP responses."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except APIError as e:
            # API errors already have status codes and formatted messages
            return JSONResponse(
                status_code=e.http_status_code,
                content={
                    "error": {
                        "code": e.error_code,
                        "message": str(e),
                        "details": e.details if e.details else None,
                        "suggestions": e.suggestions if e.suggestions else None
                    }
                }
            )
        except HTTPException as e:
            # Pass through FastAPI's HTTPExceptions
            raise
        except Exception as e:
            # Wrap unknown errors as InternalServerError
            error = InternalServerError(
                message=str(e),
                context=ErrorContext(
                    source="api_error_handler",
                    severity=ErrorSeverity.ERROR,
                    additional_data={"original_error": str(e)}
                )
            )
            return JSONResponse(
                status_code=error.http_status_code,
                content={
                    "error": {
                        "code": error.error_code,
                        "message": str(error),
                        "details": error.details if error.details else None,
                        "suggestions": error.suggestions if error.suggestions else None
                    }
                }
            )
    return wrapper

class APIError(BaseError):
    """Base class for all API-related errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        http_status_code: int = 500,
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None
    ):
        if not error_code.startswith('API-'):
            error_code = f"API-{error_code}"
        super().__init__(
            message,
            error_code,
            http_status_code,
            context,
            details,
            suggestions
        )
        self.set_severity(ErrorSeverity.ERROR)


class RequestError(APIError):
    """Request validation and processing errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "API-REQ-VAL-001",
        http_status_code: int = 400,
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message,
            error_code,
            http_status_code,
            context,
            details,
            suggestions=[
                "Check request format and content",
                "Verify required fields are present",
                "Ensure data types are correct"
            ]
        )


class ResponseError(APIError):
    """Response generation and processing errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "API-RES-GEN-001",
        http_status_code: int = 500,
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message,
            error_code,
            http_status_code,
            context,
            details,
            suggestions=[
                "Check server response format",
                "Verify response processing logic",
                "Ensure all required data is returned"
            ]
        )
        self.set_severity(ErrorSeverity.ERROR)


class NotFoundError(APIError):
    """Resource not found errors."""
    
    def __init__(
        self,
        message: str,
        resource_type: str,
        resource_id: str,
        error_code: str = "API-RES-NFD-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            'resource_type': resource_type,
            'resource_id': resource_id
        })
        
        super().__init__(
            message,
            error_code,
            http_status_code=404,
            context=context,
            details=details,
            suggestions=[
                f"Verify {resource_type} ID is correct",
                f"Check if {resource_type} exists",
                "Ensure you have access permissions"
            ]
        )
        self.set_severity(ErrorSeverity.WARNING)


class InternalServerError(APIError):
    """Internal server errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "API-INT-FAIL-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message,
            error_code,
            http_status_code=500,
            context=context,
            details=details,
            suggestions=[
                "Check server logs for details",
                "Verify server configuration",
                "Contact system administrator"
            ]
        )
        self.set_severity(ErrorSeverity.ERROR)


class ExternalAPIError(APIError):
    """Error raised when external API integration fails."""
    
    def __init__(
        self,
        message: str,
        api_name: str,
        operation: str,
        error_code: str = "API-EXT-FAIL-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the error.
        
        Args:
            message: Error message
            api_name: Name of the external API
            operation: Operation being performed
            error_code: Error code (default: API-EXT-FAIL-001)
            context: Error context
            details: Additional error details
        """
        if details is None:
            details = {}
        details.update({
            "api_name": api_name,
            "operation": operation
        })
        
        super().__init__(
            message=message,
            error_code=error_code,
            http_status_code=502,  # Bad Gateway
            context=context,
            details=details,
            suggestions=[
                "Check if the external API service is available",
                "Verify your API credentials and permissions",
                "Review the request format and parameters",
                "Check the API documentation for any changes"
            ]
        )
        self.set_severity(ErrorSeverity.ERROR)


class ValidationError(APIError):
    """API request validation failures."""
    
    def __init__(
        self,
        message: str,
        field: str,
        validation_type: str,
        error_code: str = "API-VAL-FAIL-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            'field': field,
            'validation_type': validation_type
        })
        
        super().__init__(
            message,
            error_code,
            http_status_code=400,
            context=context,
            details=details,
            suggestions=[
                f"Check {field} format and requirements",
                "Verify input constraints",
                "Review API documentation"
            ]
        )
        self.set_severity(ErrorSeverity.WARNING)


class AuthenticationError(APIError):
    """API authentication failures."""
    
    def __init__(
        self,
        message: str,
        auth_type: str,
        error_code: str = "API-AUTH-FAIL-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            'auth_type': auth_type
        })
        
        super().__init__(
            message,
            error_code,
            http_status_code=401,
            context=context,
            details=details,
            suggestions=[
                "Check API credentials",
                "Verify authentication method",
                "Review token expiration"
            ]
        )
        self.set_severity(ErrorSeverity.ERROR)


class AuthorizationError(APIError):
    """API authorization failures."""
    
    def __init__(
        self,
        message: str,
        required_permission: str,
        error_code: str = "API-AUTH-FAIL-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            'required_permission': required_permission
        })
        
        super().__init__(
            message,
            error_code,
            http_status_code=403,
            context=context,
            details=details,
            suggestions=[
                "Check API access level",
                "Verify required permissions",
                "Request necessary access"
            ]
        )
        self.set_severity(ErrorSeverity.ERROR) 