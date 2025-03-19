"""
User Error Handling

This module defines user-specific errors extending the base error system.
"""

from typing import Optional, Dict, Any, List

from .base import BaseError, ErrorContext, ErrorSeverity


class UserError(BaseError):
    """Base class for all user-related errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        http_status_code: int = 400,
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None
    ):
        if not error_code.startswith('USER-'):
            error_code = f"USER-{error_code}"
        super().__init__(
            message,
            error_code,
            http_status_code,
            context,
            details,
            suggestions
        )


class UserNotFoundError(UserError):
    """Error raised when a user cannot be found."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "USER-NFD-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            http_status_code=404,  # Not Found
            context=context,
            details=details,
            suggestions=[
                "Check if the user ID or email is correct",
                "Verify the user exists in the system",
                "Ensure you have the correct credentials"
            ]
        )
        self.set_severity(ErrorSeverity.ERROR)


class UserRegistrationError(UserError):
    """User registration process failures."""
    
    def __init__(
        self,
        message: str,
        registration_step: str,
        error_code: str = "USER-REG-FAIL-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            'registration_step': registration_step
        })
        
        super().__init__(
            message,
            error_code,
            http_status_code=400,
            context=context,
            details=details,
            suggestions=[
                "Check registration requirements",
                "Verify email format",
                "Ensure password meets criteria"
            ]
        )
        self.set_severity(ErrorSeverity.WARNING)


class UserProfileError(UserError):
    """User profile management failures."""
    
    def __init__(
        self,
        message: str,
        profile_field: str,
        error_code: str = "USER-PROF-FAIL-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            'profile_field': profile_field
        })
        
        super().__init__(
            message,
            error_code,
            http_status_code=400,
            context=context,
            details=details,
            suggestions=[
                "Check field requirements",
                "Verify data format",
                "Ensure field permissions"
            ]
        )
        self.set_severity(ErrorSeverity.WARNING)


class UserPreferencesError(UserError):
    """User preferences management failures."""
    
    def __init__(
        self,
        message: str,
        preference_key: str,
        error_code: str = "USER-PREF-FAIL-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            'preference_key': preference_key
        })
        
        super().__init__(
            message,
            error_code,
            http_status_code=400,
            context=context,
            details=details,
            suggestions=[
                "Check preference options",
                "Verify setting format",
                "Review preference constraints"
            ]
        )
        self.set_severity(ErrorSeverity.WARNING)


class UserSubscriptionError(UserError):
    """User subscription management failures."""
    
    def __init__(
        self,
        message: str,
        subscription_type: str,
        operation: str,
        error_code: str = "USER-SUB-FAIL-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            'subscription_type': subscription_type,
            'operation': operation
        })
        
        super().__init__(
            message,
            error_code,
            http_status_code=400,
            context=context,
            details=details,
            suggestions=[
                "Check subscription status",
                "Verify payment information",
                "Review subscription terms"
            ]
        )
        self.set_severity(ErrorSeverity.ERROR)


class UserValidationError(BaseError):
    """Error raised when user data validation fails."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "USER-VAL-FAIL-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error.
        
        Args:
            message: Error message
            error_code: Error code (default: USER-VAL-FAIL-001)
            context: Error context
            details: Additional error details
        """
        super().__init__(
            message=message,
            error_code=error_code,
            http_status_code=400,
            context=context,
            details=details,
            severity=ErrorSeverity.ERROR,
            suggestions=[
                "Check that all required fields are provided",
                "Ensure field values meet validation requirements",
                "Verify email format is correct",
                "Check password meets complexity requirements"
            ]
        ) 