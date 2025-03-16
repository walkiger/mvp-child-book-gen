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
import sqlite3
from typing import Any, Callable, Optional, TypeVar

# Import from shared error handling utilities
from utils.error_handling import (
    BaseError, ErrorSeverity, setup_logger, handle_error,
    ServerError, DatabaseError, ConfigError, ResourceError,
    InputError, ImageError, with_error_handling as shared_error_handling
)
from utils.error_templates import (
    DATABASE_NOT_FOUND, SERVER_START_ERROR, SERVER_STOP_ERROR,
    PROCESS_NOT_FOUND, CONFIG_NOT_FOUND, INVALID_CONFIG
)

T = TypeVar("T")

# Create process error that's specific to management package
class ProcessError(BaseError):
    """Custom exception for management CLI process errors"""
    def __init__(self, message: str, pid: Optional[int] = None, severity: str = "ERROR",
                 details: Optional[str] = None, error_code: str = "E-PRO-001"):
        super().__init__(message, severity, details, error_code)
        self.pid = pid
        self.status_code = 500  # Internal server error


# Decorator for error handling - wrapper around the shared implementation
def with_error_handling(context: Optional[str] = None, exit_on_error: bool = True) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Standardize error handling for management functions"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        return shared_error_handling(func, logger_name="management", context=context, exit_on_error=exit_on_error)
    return decorator


# Database-specific error handling decorator
def db_error_handler(func: Callable[..., T]) -> Callable[..., T]:
    """Handle database errors and convert them to DatabaseError instances"""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        logger = setup_logger("management")
        try:
            return func(*args, **kwargs)
        except DatabaseError as e:
            # Re-raise DatabaseError instances without modification
            handle_error(e, logger, True)
            raise
        except sqlite3.OperationalError as e:
            db_path = args[0] if args else None
            error_msg = str(e).lower()
            if "database is locked" in error_msg:
                error = DatabaseError("Database is locked", db_path=db_path)
            elif "permission denied" in error_msg or "readonly database" in error_msg:
                error = DatabaseError("Permission denied", db_path=db_path)
            elif "unable to open database file" in error_msg:
                # Check if it's a permission error
                if db_path and os.path.exists(os.path.dirname(db_path)):
                    try:
                        # Try to write a test file in the directory
                        test_file = os.path.join(os.path.dirname(db_path), ".test")
                        with open(test_file, "w") as f:
                            f.write("")
                        os.remove(test_file)
                    except (OSError, PermissionError):
                        error = DatabaseError("Permission denied", db_path=db_path)
                    else:
                        error = DatabaseError("Could not connect to database", db_path=db_path)
                else:
                    error = DatabaseError("Could not connect to database", db_path=db_path)
            else:
                error = DatabaseError(error_msg, db_path=db_path)
            handle_error(error, logger, True)
            raise error
        except sqlite3.IntegrityError as e:
            db_path = args[0] if args else None
            error = DatabaseError("Integrity error", db_path=db_path)
            handle_error(error, logger, True)
            raise error
        except sqlite3.DatabaseError as e:
            db_path = args[0] if args else None
            error_msg = str(e).lower()
            if "file is not a database" in error_msg:
                error = DatabaseError("Database is corrupted", db_path=db_path)
            else:
                error = DatabaseError("Database error", db_path=db_path)
            handle_error(error, logger, True)
            raise error
        except Exception as e:
            db_path = args[0] if args else None
            error = DatabaseError("Unexpected error", db_path=db_path)
            handle_error(error, logger, True)
            raise error
    return wrapper