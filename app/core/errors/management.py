"""
Management-specific error classes and error handling utilities.

This module provides error handling for management operations including
process management, database operations, and server management.
"""

from datetime import datetime, UTC
from typing import Optional, Dict, Any, List
from uuid import uuid4

from .base import BaseError, ErrorContext, ErrorSeverity

class ManagementError(BaseError):
    """Base class for all management-related errors"""
    def __init__(
        self,
        message: str,
        error_code: str,
        http_status_code: int = 500,
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None
    ):
        if not error_code.startswith('MGT-'):
            error_code = f"MGT-{error_code}"
        if context is None:
            context = ErrorContext(
                source="management",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data=details or {}
            )
        super().__init__(
            message,
            error_code,
            http_status_code,
            context,
            details,
            suggestions
        )
        self.set_severity(ErrorSeverity.ERROR)


class ProcessError(ManagementError):
    """Error raised for process management issues"""
    def __init__(
        self,
        message: str,
        pid: Optional[int] = None,
        error_code: str = "MGT-PROC-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if pid is not None:
            details["pid"] = pid
        
        super().__init__(
            message,
            error_code,
            http_status_code=500,
            context=context,
            details=details,
            suggestions=[
                "Check process status",
                "Verify process permissions",
                "Check system resources"
            ]
        )
        self.pid = pid


class ServerError(ManagementError):
    """Error raised for server management issues"""
    def __init__(
        self,
        message: str,
        server: Optional[str] = None,
        error_code: str = "MANAGEMENT-SERVER-GENERAL-001",
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        context: Optional[ErrorContext] = None
    ):
        additional_data = {"server": server} if server is not None else {}
        super().__init__(
            message,
            error_code=error_code,
            http_status_code=500,
            context=context,
            details=additional_data
        )
        self.server = server


class CommandError(ManagementError):
    """Error raised for command execution issues"""
    def __init__(
        self,
        message: str,
        command: Optional[str] = None,
        error_code: str = "MANAGEMENT-COMMAND-GENERAL-001",
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        context: Optional[ErrorContext] = None
    ):
        additional_data = {"command": command} if command is not None else {}
        super().__init__(
            message,
            error_code=error_code,
            http_status_code=500,
            context=context,
            details=additional_data
        )
        self.command = command


class EnvironmentError(ManagementError):
    """Error raised for environment management issues"""
    def __init__(
        self,
        message: str,
        env_var: Optional[str] = None,
        error_code: str = "MANAGEMENT-ENVIRONMENT-GENERAL-001",
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        context: Optional[ErrorContext] = None
    ):
        additional_data = {"env_var": env_var} if env_var is not None else {}
        super().__init__(
            message,
            error_code=error_code,
            http_status_code=500,
            context=context,
            details=additional_data
        )
        self.env_var = env_var


class MonitoringError(ManagementError):
    """Error raised for monitoring operation issues"""
    def __init__(
        self,
        message: str,
        metric: Optional[str] = None,
        error_code: str = "MANAGEMENT-MONITORING-GENERAL-001",
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        context: Optional[ErrorContext] = None
    ):
        additional_data = {"metric": metric} if metric is not None else {}
        super().__init__(
            message,
            error_code=error_code,
            http_status_code=500,
            context=context,
            details=additional_data
        )
        self.metric = metric


class ManagementDatabaseError(ManagementError):
    """Error raised for management database operations"""
    def __init__(
        self,
        message: str,
        db_path: Optional[str] = None,
        error_code: str = "MANAGEMENT-DATABASE-GENERAL-001",
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        context: Optional[ErrorContext] = None
    ):
        additional_data = {"db_path": db_path} if db_path is not None else {}
        super().__init__(
            message,
            error_code=error_code,
            http_status_code=500,
            context=context,
            details=additional_data
        )
        self.db_path = db_path


def with_management_error_handling(func):
    """Decorator for standardized management error handling"""
    from functools import wraps
    import inspect
    
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ManagementError as e:
            # Already properly formatted, just re-raise
            raise
        except Exception as e:
            context = ErrorContext(
                source="management",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={
                    "function": func.__name__,
                    "args": str(args),
                    "kwargs": str(kwargs),
                    "error": str(e)
                }
            )
            raise ManagementError(
                str(e),
                error_code="MANAGEMENT-GENERAL-UNEXPECTED-001",
                context=context
            ) from e
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ManagementError as e:
            # Already properly formatted, just re-raise
            raise
        except Exception as e:
            context = ErrorContext(
                source="management",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={
                    "function": func.__name__,
                    "args": str(args),
                    "kwargs": str(kwargs),
                    "error": str(e)
                }
            )
            raise ManagementError(
                str(e),
                error_code="MANAGEMENT-GENERAL-UNEXPECTED-001",
                context=context
            ) from e
    
    # Return appropriate wrapper based on whether the function is async or not
    return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper 