"""
Shared error handling utilities for both app and management packages.

This module provides a unified error handling approach that can be used by 
both the FastAPI application and the management CLI tools.
"""

import os
import sys
import time
import logging
import traceback
from enum import Enum
from functools import wraps
from typing import Dict, Optional, Any, Callable, Type, Tuple, List

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)


class ErrorSeverity(Enum):
    """Enum representing the severity levels of errors"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class BaseError(Exception):
    """Base exception class for all application errors"""
    
    def __init__(self, 
                 message: str, 
                 severity: ErrorSeverity = ErrorSeverity.ERROR,
                 details: Optional[str] = None, 
                 error_code: Optional[str] = None,
                 http_status_code: Optional[int] = None,
                 **kwargs):
        """Initialize a base error
        
        Args:
            message: Error message
            severity: Error severity level
            details: Additional error details or context
            error_code: Unique error code
            http_status_code: HTTP status code to use in API responses
            **kwargs: Additional error context as key-value pairs
        """
        self.message = message
        self.severity = severity
        self.details = details
        self.error_code = error_code or "E-GEN-001"
        self.http_status_code = http_status_code or 500
        self.kwargs = kwargs
        super().__init__(self.format_message())
    
    def format_message(self) -> str:
        """Format the error message with severity and code prefix"""
        if self.details:
            return f"{self.severity.value} [{self.error_code}]: {self.message} - {self.details}"
        return f"{self.severity.value} [{self.error_code}]: {self.message}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format for API responses"""
        result = {
            "error_code": self.error_code,
            "severity": self.severity.value,
            "message": self.message,
        }
        
        if self.details:
            result["details"] = self.details
            
        if self.kwargs:
            result["context"] = self.kwargs
            
        return result


# Specific error subclasses

class ServerError(BaseError):
    """Exception raised for server-related errors"""
    
    def __init__(self, message, server_type=None, severity=ErrorSeverity.ERROR, details=None, **kwargs):
        if server_type:
            message = f"{server_type.upper()} server: {message}"
        
        super().__init__(
            message=message,
            error_code=kwargs.pop("error_code", "E-SRV-001"),
            http_status_code=kwargs.pop("http_status_code", 503),  # Service Unavailable
            severity=severity,
            details=details,
            server_type=server_type,
            **kwargs
        )


class ProcessError(BaseError):
    """Exception raised for process-related errors"""
    
    def __init__(self, message, process_name=None, **kwargs):
        if process_name:
            message = f"Process '{process_name}': {message}"
        
        super().__init__(
            message=message,
            error_code=kwargs.pop("error_code", "E-PRO-001"),
            http_status_code=kwargs.pop("http_status_code", 500),  # Internal Server Error
            severity=kwargs.pop("severity", ErrorSeverity.ERROR),
            process_name=process_name,
            **kwargs
        )


class DatabaseError(BaseError):
    """Exception raised for database-related errors"""
    
    def __init__(self, message, db_path=None, **kwargs):
        self.db_path = db_path
        self.message = message  # Store the original message
        super().__init__(
            message=message,
            error_code=kwargs.pop("error_code", "E-DB-001"),
            http_status_code=kwargs.pop("http_status_code", 503),  # Service Unavailable
            severity=kwargs.pop("severity", ErrorSeverity.ERROR),
            db_path=db_path,
            **kwargs
        )
    
    def format_message(self) -> str:
        """Override to return just the message without severity and code prefix"""
        return self.message

    def __str__(self) -> str:
        """Override to return just the message without severity and code prefix"""
        return self.message


class ConfigError(BaseError):
    """Exception raised for configuration-related errors"""
    
    def __init__(self, message, config_item=None, **kwargs):
        if config_item:
            message = f"Configuration '{config_item}': {message}"
        
        super().__init__(
            message=message,
            error_code=kwargs.pop("error_code", "E-CFG-001"),
            http_status_code=kwargs.pop("http_status_code", 500),  # Internal Server Error
            severity=kwargs.pop("severity", ErrorSeverity.ERROR),
            config_item=config_item,
            **kwargs
        )


class ResourceError(BaseError):
    """Exception raised for resource-related errors"""
    
    def __init__(self, message, resource_name=None, **kwargs):
        if resource_name:
            message = f"Resource '{resource_name}': {message}"
        
        super().__init__(
            message=message,
            error_code=kwargs.pop("error_code", "E-RES-001"),
            http_status_code=kwargs.pop("http_status_code", 404),  # Not Found
            severity=kwargs.pop("severity", ErrorSeverity.ERROR),
            resource_name=resource_name,
            **kwargs
        )


class InputError(BaseError):
    """Exception raised for input validation errors"""
    
    def __init__(self, message, param_name=None, **kwargs):
        if param_name:
            message = f"Input parameter '{param_name}': {message}"
        
        super().__init__(
            message=message,
            error_code=kwargs.pop("error_code", "E-INP-001"),
            http_status_code=kwargs.pop("http_status_code", 422),  # Unprocessable Entity
            severity=kwargs.pop("severity", ErrorSeverity.ERROR),
            param_name=param_name,
            **kwargs
        )


class AuthError(BaseError):
    """Exception raised for authentication and authorization errors"""
    
    def __init__(self, message, **kwargs):
        super().__init__(
            message=message,
            error_code=kwargs.pop("error_code", "E-AUTH-001"),
            http_status_code=kwargs.pop("http_status_code", 401),  # Unauthorized
            severity=kwargs.pop("severity", ErrorSeverity.ERROR),
            **kwargs
        )


class ImageError(BaseError):
    """Exception raised for image processing errors"""
    
    def __init__(self, message, image_path=None, **kwargs):
        if image_path:
            message = f"Image '{image_path}': {message}"
        
        super().__init__(
            message=message,
            error_code=kwargs.pop("error_code", "E-IMG-001"),
            http_status_code=kwargs.pop("http_status_code", 500),  # Internal Server Error
            severity=kwargs.pop("severity", ErrorSeverity.ERROR),
            image_path=image_path,
            **kwargs
        )


# Error handling utilities

def setup_logger(name="app", log_file="logs/app.log", level=logging.INFO):
    """Set up and return a logger with file and console handlers
    
    Args:
        name: Logger name
        log_file: Path to the log file
        level: Logging level (default: INFO)
        
    Returns:
        Logger: Configured logger instance
    """
    # Ensure logs directory exists
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    logger = logging.getLogger(name)
    # Avoid adding handlers multiple times
    if not logger.handlers:
        logger.setLevel(level)
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(
            '%(levelname)s: %(message)s'
        ))
        logger.addHandler(console_handler)
    
    return logger


def handle_error(error, logger=None, exit_app=False):
    """Handle an error appropriately based on its severity
    
    Args:
        error: The error to handle (exception or string message)
        logger: Optional logger to use (creates one if not provided)
        exit_app: Whether to exit the application after handling
    """
    if logger is None:
        logger = setup_logger()
    
    # Convert non-BaseError exceptions to BaseError
    if isinstance(error, Exception) and not isinstance(error, BaseError):
        tb = traceback.format_exc()
        error = BaseError(str(error), ErrorSeverity.ERROR, tb, "E-GEN-999")
    
    # Handle string messages
    if isinstance(error, str):
        logger.error(error)
        if exit_app:
            sys.exit(1)
        return
    
    # Log based on severity and possibly exit
    error_message = str(error)
    if error.severity == ErrorSeverity.INFO:
        logger.info(error_message)
    elif error.severity == ErrorSeverity.WARNING:
        logger.warning(error_message)
    elif error.severity == ErrorSeverity.ERROR:
        logger.error(error_message)
        if exit_app and not os.environ.get("PYTEST_CURRENT_TEST"):
            sys.exit(1)
    elif error.severity == ErrorSeverity.CRITICAL:
        logger.critical(error_message)
        # Always exit on critical errors
        sys.exit(1)

    # Re-raise the error
    raise error


# Decorators

def with_error_handling(func=None, context=None, exit_on_error=False, logger_name="app"):
    """Decorator to standardize error handling for functions
    
    Args:
        func: The function to decorate
        context: Optional context information for error messages
        exit_on_error: Whether to exit the program on error
        logger_name: Name for the logger to use
    
    Returns:
        The decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = setup_logger(logger_name)
            try:
                return func(*args, **kwargs)
            except BaseError as e:
                # Already formatted, just handle it
                handle_error(e, logger, exit_on_error)
                raise  # Re-raise to allow other handlers to catch it
            except FileNotFoundError as e:
                # Convert to appropriate error type
                ctx = context or func.__name__
                # Check if first arg might be a database path
                db_path = None
                if args and isinstance(args[0], str) and ('db' in func.__name__.lower() or 'database' in func.__name__.lower()):
                    db_path = args[0]
                
                if db_path:
                    error = DatabaseError(
                        f"Database file not found: {str(e)}", 
                        db_path=db_path,
                        error_code="E-DB-404"  # Not Found error code
                    )
                else:
                    error = ResourceError(
                        f"File not found: {str(e)}",
                        error_code="E-RES-404"  # Not Found error code
                    )
                handle_error(error, logger, exit_on_error)
                raise error  # Re-raise to allow other handlers to catch it
            except Exception as e:
                # Convert to BaseError with context
                ctx = context or func.__name__
                error = BaseError(
                    f"{ctx}: {str(e)}", 
                    ErrorSeverity.ERROR, 
                    traceback.format_exc(),
                    "E-GEN-500"  # Generic internal error code
                )
                handle_error(error, logger, exit_on_error)
                raise error  # Re-raise to allow other handlers to catch it
        return wrapper
        
    if func is None:
        # Called with arguments
        return decorator
    # Called without arguments
    return decorator(func)


def with_retry(max_attempts=3, retry_delay=1.0, backoff_factor=2.0, 
               exceptions=(Exception,), on_retry=None):
    """Decorator to retry functions that may experience transient failures
    
    Args:
        max_attempts: Maximum number of retry attempts
        retry_delay: Initial delay between retries (in seconds)
        backoff_factor: Factor by which to increase delay on each retry
        exceptions: Tuple of exception types to catch and retry
        on_retry: Optional callback function for retry events
    
    Returns:
        Decorated function with retry logic
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 1
            current_delay = retry_delay
            last_exception = None
            
            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        # We've exhausted all retry attempts
                        raise
                    
                    # Call the retry callback if provided
                    if on_retry:
                        on_retry(attempt, e, current_delay)
                    
                    # Log the retry
                    logger = setup_logger()
                    logger.warning(
                        f"Retry {attempt}/{max_attempts-1} for {func.__name__}: {str(e)}. "
                        f"Retrying in {current_delay:.1f} seconds..."
                    )
                    
                    # Wait before retrying
                    time.sleep(current_delay)
                    
                    # Increase delay for next attempt
                    current_delay *= backoff_factor
                    attempt += 1
                    
        return wrapper
    return decorator


# Context managers

class ManagedResource:
    """Context manager for resources that need proper cleanup"""
    
    def __init__(self, resource_name, resource_getter, cleanup_func):
        """Initialize the managed resource
        
        Args:
            resource_name: Name of the resource (for logging)
            resource_getter: Function that acquires the resource
            cleanup_func: Function that cleans up the resource
        """
        self.resource_name = resource_name
        self.resource_getter = resource_getter
        self.cleanup_func = cleanup_func
        self.resource = None
        self.logger = setup_logger()
    
    def __enter__(self):
        """Acquire the resource"""
        try:
            self.resource = self.resource_getter()
            return self.resource
        except Exception as e:
            self.logger.error(f"Error acquiring resource {self.resource_name}: {str(e)}")
            raise ResourceError(
                f"Failed to acquire {self.resource_name}",
                resource_name=self.resource_name,
                details=str(e)
            )
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up the resource"""
        if self.resource:
            try:
                self.cleanup_func(self.resource)
            except Exception as cleanup_err:
                self.logger.error(f"Error cleaning up {self.resource_name}: {str(cleanup_err)}")
                # Don't suppress the original exception if there was one
                if not exc_type:
                    raise ResourceError(
                        f"Failed to clean up {self.resource_name}",
                        resource_name=self.resource_name,
                        details=str(cleanup_err)
                    )


# FastAPI integration 

def register_exception_handlers(app):
    """Register exception handlers for FastAPI app
    
    Args:
        app: FastAPI application instance
    """
    from fastapi import Request
    from fastapi.responses import JSONResponse
    
    @app.exception_handler(BaseError)
    async def handle_base_error(request: Request, exc: BaseError):
        """Handle BaseError exceptions and convert to appropriate HTTP responses"""
        status_code = exc.http_status_code
        return JSONResponse(
            status_code=status_code,
            content=exc.to_dict()
        )
    
    @app.exception_handler(Exception)
    async def handle_generic_exception(request: Request, exc: Exception):
        """Handle unexpected exceptions and provide a consistent error response"""
        logger = setup_logger("api")
        logger.error(f"Unhandled exception: {str(exc)}\n{traceback.format_exc()}")
        
        # Convert to a BaseError
        error = BaseError(
            message="An unexpected error occurred",
            error_code="E-API-500",
            details=str(exc) if app.debug else None,
            severity=ErrorSeverity.ERROR
        )
        
        return JSONResponse(
            status_code=500,
            content=error.to_dict()
        )


# Circuit breaker pattern for external services

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "CLOSED"     # Normal operation, requests pass through
    OPEN = "OPEN"         # Service is down, fail immediately
    HALF_OPEN = "HALF_OPEN"  # Testing if service is available again


class CircuitBreaker:
    """Circuit breaker pattern implementation for external services"""
    
    def __init__(self, name, failure_threshold=5, reset_timeout=30, 
                 excluded_exceptions=None):
        """Initialize the circuit breaker
        
        Args:
            name: Name of the service (for logging)
            failure_threshold: Number of failures before opening circuit
            reset_timeout: Seconds to wait before allowing test requests
            excluded_exceptions: Exceptions that don't count as failures
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.excluded_exceptions = excluded_exceptions or ()
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self.logger = setup_logger()
    
    def __call__(self, func):
        """Decorate a function with circuit breaker protection"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            if self.state == CircuitState.OPEN:
                if time.time() - self.last_failure_time > self.reset_timeout:
                    self.logger.info(f"Circuit for {self.name} half-open, testing service...")
                    self.state = CircuitState.HALF_OPEN
                else:
                    error_msg = f"Circuit for {self.name} is open, service unavailable"
                    self.logger.warning(error_msg)
                    raise ServerError(
                        message=error_msg,
                        server_type=self.name,
                        error_code="E-CB-503",  # Circuit Breaker Service Unavailable
                        http_status_code=503  # Service Unavailable
                    )
            
            try:
                result = func(*args, **kwargs)
                
                # If the call succeeded and we were half-open, reset to closed
                if self.state == CircuitState.HALF_OPEN:
                    self.logger.info(f"Service {self.name} is available again, closing circuit")
                    self.reset()
                
                return result
                
            except self.excluded_exceptions:
                # Don't count excluded exceptions as failures
                raise
                
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if (self.state == CircuitState.CLOSED and 
                    self.failure_count >= self.failure_threshold):
                    self.logger.warning(
                        f"Circuit for {self.name} opened after {self.failure_count} failures"
                    )
                    self.state = CircuitState.OPEN
                
                # Re-raise the original exception
                raise
                
        return wrapper
    
    def reset(self):
        """Reset the circuit breaker to closed state"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0 