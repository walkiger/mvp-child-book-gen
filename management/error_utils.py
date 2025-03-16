"""
Error handling utilities for the management package
"""

import sys
import traceback
import logging
import os
from functools import wraps

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Setup basic logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/management.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("management")

class ManagementError(Exception):
    """Base exception class for management package errors"""
    def __init__(self, message, details=None):
        self.message = message
        self.details = details
        super().__init__(message)

class DatabaseError(ManagementError):
    """Exception raised for database-related errors"""
    pass

class ServerError(ManagementError):
    """Exception raised for server-related errors"""
    pass

class ConfigError(ManagementError):
    """Exception raised for configuration-related errors"""
    pass

def log_error(e, context=""):
    """Log an error with optional context information
    
    Args:
        e: The exception to log
        context: Optional context information
    """
    error_type = type(e).__name__
    error_message = str(e)
    
    if context:
        logger.error(f"{context}: {error_type} - {error_message}")
    else:
        logger.error(f"{error_type} - {error_message}")
    
    # Log traceback at debug level
    logger.debug(traceback.format_exc())
    
    # Print to console
    if context:
        print(f"Error in {context}: {error_message}", file=sys.stderr)
    else:
        print(f"Error: {error_message}", file=sys.stderr)
    
    sys.stderr.flush()

def handle_errors(func=None, context=None, exit_on_error=False):
    """Decorator to standardize error handling for functions
    
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
            except ManagementError as e:
                # Handle our custom exceptions
                log_error(e, context or func.__name__)
                if exit_on_error:
                    sys.exit(1)
                return False
            except Exception as e:
                # Handle unexpected exceptions
                log_error(e, context or func.__name__)
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
            # Convert to DatabaseError and re-raise
            raise DatabaseError(f"Database operation failed: {str(e)}", details=str(e))
    return wrapper 