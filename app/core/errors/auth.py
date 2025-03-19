"""
Authentication and Authorization Error Handling

This module defines auth-specific errors extending the base error system.
"""

from typing import Optional, Dict, Any, List

from .base import BaseError, ErrorContext, ErrorSeverity


class AuthError(BaseError):
    """Base class for all authentication/authorization errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        http_status_code: int = 401,
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None
    ):
        if not error_code.startswith('AUTH-'):
            error_code = f"AUTH-{error_code}"
        super().__init__(
            message,
            error_code,
            http_status_code,
            context,
            details,
            suggestions
        )
        self.set_severity(ErrorSeverity.ERROR)


class AuthenticationError(AuthError):
    """Authentication failures."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "AUTH-CRED-FAIL-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message,
            error_code,
            http_status_code=401,
            context=context,
            details=details,
            suggestions=[
                "Verify your credentials",
                "Check if your token has expired",
                "Ensure you are using the correct authentication method"
            ]
        )
        self.set_severity(ErrorSeverity.ERROR)


class AuthorizationError(AuthError):
    """Authorization/permission failures."""
    
    def __init__(
        self,
        message: str,
        required_permission: str,
        error_code: str = "AUTH-PERM-DENY-001",
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
                f"Request access to {required_permission}",
                "Check your role assignments",
                "Contact administrator for permissions"
            ]
        )
        self.set_severity(ErrorSeverity.ERROR)


class TokenError(AuthError):
    """Token validation/processing errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "AUTH-TOKEN-FAIL-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message,
            error_code,
            http_status_code=401,
            context=context,
            details=details,
            suggestions=[
                "Refresh your authentication token",
                "Re-authenticate to get a new token",
                "Check token expiration time"
            ]
        )
        self.set_severity(ErrorSeverity.ERROR)


class SessionError(AuthError):
    """Session management errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "AUTH-SESS-FAIL-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message,
            error_code,
            http_status_code=401,
            context=context,
            details=details,
            suggestions=[
                "Try logging in again",
                "Clear your session data",
                "Check session timeout settings"
            ]
        )
        self.set_severity(ErrorSeverity.ERROR)


class AuthValidationError(AuthError):
    """Authentication data validation errors."""
    
    def __init__(
        self,
        message: str,
        field: str,
        error_code: str = "AUTH-VAL-FAIL-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            'field': field
        })
        
        super().__init__(
            message,
            error_code,
            http_status_code=400,  # Bad Request for validation errors
            context=context,
            details=details,
            suggestions=[
                f"Check the format of {field}",
                "Verify input requirements",
                "Ensure all required fields are provided"
            ]
        )
        self.set_severity(ErrorSeverity.ERROR)


class RegistrationError(AuthError):
    """Error raised when user registration fails."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "AUTH-REG-FAIL-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error.
        
        Args:
            message: Error message
            error_code: Error code (default: AUTH-REG-FAIL-001)
            context: Error context
            details: Additional error details
        """
        super().__init__(
            message=message,
            error_code=error_code,
            http_status_code=400,
            context=context,
            details=details,
            suggestions=[
                "Check that all required registration fields are provided",
                "Ensure the email address is not already registered",
                "Verify password meets security requirements",
                "Check for any validation errors in the registration data"
            ]
        )
        self.set_severity(ErrorSeverity.ERROR)