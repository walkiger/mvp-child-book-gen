"""
Error classes for monitoring functionality.
"""

from datetime import datetime, UTC
from typing import Optional, Dict, Any
from uuid import uuid4

from .base import BaseError, ErrorContext, ErrorSeverity

class MonitoringError(BaseError):
    """Base class for monitoring-related errors."""
    def __init__(
        self,
        message: str,
        error_code: str = "MON-GEN-001",
        context: Optional[ErrorContext] = None
    ):
        if context is None:
            context = ErrorContext(
                source="monitoring",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4())
            )
        super().__init__(message, error_code, context)

class MetricsError(MonitoringError):
    """Error raised when there's an issue collecting metrics."""
    def __init__(
        self,
        message: str,
        error_code: str = "MON-METRICS-001",
        context: Optional[ErrorContext] = None,
        metrics_type: Optional[str] = None
    ):
        if context is None:
            context = ErrorContext(
                source="monitoring.metrics",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"metrics_type": metrics_type} if metrics_type else None
            )
        super().__init__(message, error_code, context)

class LogAnalysisError(MonitoringError):
    """Error raised when there's an issue analyzing logs."""
    def __init__(
        self,
        message: str,
        error_code: str = "MON-LOGS-001",
        context: Optional[ErrorContext] = None,
        log_type: Optional[str] = None
    ):
        if context is None:
            context = ErrorContext(
                source="monitoring.logs",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"log_type": log_type} if log_type else None
            )
        super().__init__(message, error_code, context)

class RouteHealthError(MonitoringError):
    """Error raised when there's an issue checking route health."""
    def __init__(
        self,
        message: str,
        error_code: str = "MON-ROUTE-001",
        context: Optional[ErrorContext] = None,
        route: Optional[str] = None,
        status_code: Optional[int] = None
    ):
        if context is None:
            context = ErrorContext(
                source="monitoring.route_health",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={
                    "route": route,
                    "status_code": status_code
                } if route else None
            )
        super().__init__(message, error_code, context)

class ServerStatusError(MonitoringError):
    """Error raised when there's an issue checking server status."""
    def __init__(
        self,
        message: str,
        error_code: str = "MON-SERVER-001",
        context: Optional[ErrorContext] = None,
        server_type: Optional[str] = None
    ):
        if context is None:
            context = ErrorContext(
                source="monitoring.server_status",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"server_type": server_type} if server_type else None
            )
        super().__init__(message, error_code, context) 