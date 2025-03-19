"""
Error handling utilities for the management package
"""

import sys
import traceback
import logging
import os
from functools import wraps
from typing import Optional, Dict, Any

from app.core.errors.base import BaseError, ErrorContext, ErrorSeverity
from app.core.errors.management import (
    ManagementError, ManagementDatabaseError as DatabaseError,
    ServerError, ProcessError, EnvironmentError, MonitoringError,
    with_management_error_handling
)
from app.core.logging import setup_logger

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Setup basic logging configuration
logger = setup_logger(
    name="management.error_utils",
    level="INFO",
    log_file="logs/management.log"
)

def create_error_context(
    operation: str,
    source: str = "management",
    additional_info: Optional[Dict[str, Any]] = None
) -> ErrorContext:
    """Create an error context for management operations
    
    Args:
        operation: The operation being performed
        source: Source of the error (default: management)
        additional_info: Additional context information
        
    Returns:
        ErrorContext object
    """
    context = ErrorContext(
        operation=operation,
        source=source,
        timestamp=None  # Will be set automatically
    )
    
    if additional_info:
        context.update(additional_info)
    
    return context

def log_error(error: BaseError, context: Optional[str] = None):
    """Log an error with optional context information
    
    Args:
        error: The BaseError instance to log
        context: Optional context string
    """
    error_type = type(error).__name__
    error_message = str(error)
    error_code = getattr(error, 'error_code', 'UNKNOWN')
    severity = getattr(error, 'severity', ErrorSeverity.ERROR)
    
    log_msg = f"{error_type}[{error_code}] - {error_message}"
    if context:
        log_msg = f"{context}: {log_msg}"
    
    if severity >= ErrorSeverity.ERROR:
        logger.error(log_msg)
    elif severity >= ErrorSeverity.WARNING:
        logger.warning(log_msg)
    else:
        logger.info(log_msg)
    
    # Log details at debug level
    if error.details:
        logger.debug(f"Error details: {error.details}")
    logger.debug(traceback.format_exc())
    
    # Print to console with suggestions if available
    print(f"Error: {error_message}", file=sys.stderr)
    if hasattr(error, 'suggestions') and error.suggestions:
        print("\nSuggestions:", file=sys.stderr)
        for suggestion in error.suggestions:
            print(f"- {suggestion}", file=sys.stderr)
    
    sys.stderr.flush()

def handle_errors(func=None, *, context: Optional[str] = None, exit_on_error: bool = False):
    """Decorator to standardize error handling for management functions
    
    Args:
        func: The function to decorate
        context: Optional context information for error messages
        exit_on_error: Whether to exit the program on error
    
    Returns:
        The decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except BaseError as e:
                # Handle our custom error hierarchy
                log_error(e, context or func.__name__)
                if exit_on_error:
                    sys.exit(1)
                return False
            except Exception as e:
                # Convert unexpected exceptions to ManagementError
                error_ctx = create_error_context(
                    operation=func.__name__,
                    additional_info={'original_error': str(e)}
                )
                management_error = ManagementError(
                    message=f"Unexpected error in management operation: {str(e)}",
                    error_code="MGT-UNEXPECTED-001",
                    context=error_ctx,
                    details={'traceback': traceback.format_exc()}
                )
                log_error(management_error, context or func.__name__)
                if exit_on_error:
                    sys.exit(1)
                return False
        return wrapper
        
    if func is None:
        # Called with arguments
        return decorator
    # Called without arguments
    return decorator(func)

def safe_db_operation(func):
    """Decorator specifically for database operations
    
    Args:
        func: The database operation function to decorate
        
    Returns:
        The decorated function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_ctx = create_error_context(
                operation=func.__name__,
                source='database',
                additional_info={'original_error': str(e)}
            )
            raise DatabaseError(
                message=f"Database operation failed: {str(e)}",
                error_code="MGT-DB-FAIL-001",
                context=error_ctx,
                details={
                    'operation': func.__name__,
                    'traceback': traceback.format_exc()
                }
            )
    return wrapper 