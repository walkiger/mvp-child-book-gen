"""
Base Error Handling

This module provides the foundation for all error handling in the application.
It defines base classes and utilities for error management.
"""

from dataclasses import dataclass, asdict
from datetime import datetime, UTC
from enum import Enum
from typing import Any, Dict, Optional, List
import uuid
import logging

# Setup logger
logger = logging.getLogger(__name__)

class ErrorSeverity(str, Enum):
    """Severity levels for errors."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class ErrorContext:
    """Context information for errors."""
    # Core Fields
    timestamp: datetime = datetime.now(UTC)
    error_id: str = str(uuid.uuid4())
    source: str = ""  # Component/module where error occurred
    severity: ErrorSeverity = ErrorSeverity.ERROR
    
    # Request Context
    request_id: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    
    # User Context
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    
    # Technical Context
    trace_id: Optional[str] = None
    stack_trace: Optional[str] = None
    additional_data: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['severity'] = self.severity.value
        return data


class BaseError(Exception):
    """Base class for application errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        http_status_code: int = 500,
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None
    ):
        """
        Initialize base error.
        
        Args:
            message: Human-readable error message
            error_code: Unique error identifier (format: DOMAIN-ENTITY-SPECIFIC-NUMBER)
            http_status_code: HTTP status code (default: 500)
            context: Error context (default: None)
            details: Additional error details (default: None)
            suggestions: List of recovery suggestions (default: None)
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.http_status_code = http_status_code
        self.context = context or ErrorContext()
        self.details = details or {}
        self.suggestions = suggestions or []
        
        # Validate error code format
        self._validate_error_code(error_code)
        
        # Log the error
        self._log_error()
    
    def _validate_error_code(self, error_code: str) -> None:
        """Validate error code format.
        
        Args:
            error_code: Error code to validate
            
        Raises:
            ValueError: If error code format is invalid
        """
        parts = error_code.split("-")
        if len(parts) < 3:
            raise ValueError(
                f"Invalid error code format: {error_code}. "
                "Expected format: DOMAIN-ENTITY-SPECIFIC-NUMBER"
            )
        
        # Check that all parts except the last are alphanumeric
        for part in parts[:-1]:
            if not part.isalnum():
                raise ValueError(
                    f"Invalid error code format: {error_code}. "
                    "All parts except the last must be alphanumeric."
                )
        
        # Check that the last part is a number
        if not parts[-1].isdigit():
            raise ValueError(
                f"Invalid error code format: {error_code}. "
                "The last part must be a number."
            )
    
    def _log_error(self) -> None:
        """Log the error with its context."""
        log_message = (
            f"[{self.error_code}] {self.message}\n"
            f"Source: {self.context.source}\n"
            f"Severity: {self.context.severity}\n"
            f"Timestamp: {self.context.timestamp}\n"
            f"Error ID: {self.context.error_id}"
        )
        
        if self.context.additional_data:
            log_message += f"\nAdditional Data: {self.context.additional_data}"
        
        if self.context.severity == ErrorSeverity.DEBUG:
            logger.debug(log_message)
        elif self.context.severity == ErrorSeverity.INFO:
            logger.info(log_message)
        elif self.context.severity == ErrorSeverity.WARNING:
            logger.warning(log_message)
        elif self.context.severity == ErrorSeverity.ERROR:
            logger.error(log_message)
        elif self.context.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format."""
        return {
            'error_code': self.error_code,
            'message': self.message,
            'http_status_code': self.http_status_code,
            'context': self.context.to_dict(),
            'details': self.details,
            'suggestions': self.suggestions
        }
    
    def add_suggestion(self, suggestion: str) -> None:
        """Add a recovery suggestion."""
        self.suggestions.append(suggestion)
    
    def add_detail(self, key: str, value: Any) -> None:
        """Add additional error detail."""
        self.details[key] = value
    
    def set_severity(self, severity: ErrorSeverity) -> None:
        """Set error severity."""
        self.context.severity = severity
    
    def should_alert(self) -> bool:
        """Whether this error should trigger alerts."""
        return self.context.severity in (ErrorSeverity.CRITICAL, ErrorSeverity.ERROR)
    
    def __str__(self) -> str:
        """String representation of the error."""
        return f"[{self.error_code}] {self.message}"


class ConfigurationError(BaseError):
    """Error raised when there are configuration issues."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        context: Optional[ErrorContext] = None
    ):
        """Initialize configuration error.
        
        Args:
            message: Error message
            error_code: Error code in format CFG-ENTITY-NUMBER
            context: Error context information
        """
        if not error_code.startswith("CFG-"):
            error_code = f"CFG-{error_code}"
        super().__init__(message, error_code, context=context) 