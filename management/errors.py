"""
Custom exceptions and error handling utilities for the management package.

This module imports and extends the shared error handling utilities from
the utils package for use in the management CLI tools.
"""

import sys
import logging
import traceback
import os
from functools import wraps

# Import from shared error handling utilities
from utils.error_handling import (
    BaseError, ErrorSeverity, setup_logger, handle_error,
    ServerError, DatabaseError, ConfigError, ResourceError,
    InputError, ImageError
)
from utils.error_templates import (
    DATABASE_NOT_FOUND, SERVER_START_ERROR, SERVER_STOP_ERROR,
    PROCESS_NOT_FOUND, CONFIG_NOT_FOUND, INVALID_CONFIG
)

# Create process error that's specific to management package
class ProcessError(BaseError):
    """Exception raised for process-related errors specific to the management CLI"""
    
    def __init__(self, message, pid=None, severity=ErrorSeverity.ERROR, details=None, error_code=None):
        self.pid = pid
        if pid:
            message = f"Process {pid}: {message}"
        error_code = error_code or "E-PRO-001"
        super().__init__(
            message=message,
            severity=severity,
            details=details,
            error_code=error_code,
            http_status_code=500,  # internal server error
            pid=pid
        )


# Decorator for error handling - wrapper around the shared implementation
def with_error_handling(func=None, context=None, exit_on_error=False):
    """Decorator to standardize error handling for management functions
    
    This is a wrapper around the shared error_handling utility with
    customizations for the management package.
    
    Args:
        func: The function to decorate
        context: Optional context information for error messages
        exit_on_error: Whether to exit the program on error
    
    Returns:
        The decorated function
    """
    from utils.error_handling import with_error_handling as shared_with_error_handling
    
    return shared_with_error_handling(
        func=func,
        context=context,
        exit_on_error=exit_on_error,
        logger_name="management"  # Use management logger
    )


# Database-specific error handling decorator
def db_error_handler(func):
    """Decorator specifically for database operations
    
    Args:
        func: The database operation function to decorate
    
    Returns:
        The decorated function with database-specific error handling
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Get the db_path argument if it's present
            db_path = None
            if args and len(args) > 0 and isinstance(args[0], str):
                db_path = args[0]
            elif 'db_path' in kwargs:
                db_path = kwargs['db_path']
                
            # Convert to DatabaseError and re-raise
            raise DatabaseError(
                "Database operation failed", 
                db_path=db_path, 
                severity=ErrorSeverity.ERROR, 
                details=str(e),
                error_code="E-DB-500"  # Database operation error
            )
    return wrapper 