"""Tests for management error handling."""

import pytest
from datetime import datetime, UTC
from uuid import UUID

from app.core.errors.management import (
    ManagementError,
    ProcessError,
    ServerError,
    CommandError,
    EnvironmentError,
    MonitoringError,
    ManagementDatabaseError,
    with_management_error_handling
)
from app.core.errors.base import ErrorContext, ErrorSeverity, RetryConfig


@pytest.fixture
def error_context():
    """Create a test error context."""
    return ErrorContext(
        source="test",
        severity=ErrorSeverity.ERROR,
        timestamp=datetime.now(UTC),
        error_id="test-id",
        additional_data={"test": "data"}
    )


def test_management_error_basic():
    """Test basic ManagementError creation."""
    error = ManagementError("test error", "MGT-TEST-001")
    assert error.message == "test error"
    assert error.error_code == "MGT-TEST-001"
    assert error.error_context.source == "management"
    assert isinstance(error.error_context.error_id, str)
    assert UUID(error.error_context.error_id)  # Validates UUID format
    assert error.error_context.severity == ErrorSeverity.ERROR
    assert error.error_context.timestamp is not None
    assert isinstance(error.error_context.timestamp, datetime)


def test_management_error_with_context(error_context):
    """Test ManagementError with provided context."""
    error = ManagementError(
        "test error",
        "MGT-TEST-001",
        error_context=error_context
    )
    assert error.error_context == error_context
    assert error.error_context.source == "test"
    assert error.error_context.additional_data["test"] == "data"


def test_process_error():
    """Test ProcessError creation and attributes."""
    pid = 12345
    error = ProcessError(
        "process failed",
        pid=pid,
        retry_config=RetryConfig(max_retries=3, delay_seconds=1)
    )
    assert error.pid == pid
    assert error.error_code == "MGT-PID-001"
    assert error.error_context.additional_data["pid"] == pid
    assert error.error_context.retry_config.max_retries == 3
    assert error.error_context.retry_config.delay_seconds == 1


def test_server_error():
    """Test ServerError creation and attributes."""
    server = "test-server"
    error = ServerError(
        "server failed",
        server=server,
        severity=ErrorSeverity.CRITICAL
    )
    assert error.server == server
    assert error.error_code == "MGT-SRV-001"
    assert error.error_context.additional_data["server"] == server
    assert error.error_context.severity == ErrorSeverity.CRITICAL


def test_command_error():
    """Test CommandError creation and attributes."""
    command = "test command"
    error = CommandError(
        "command failed",
        command=command,
        additional_data={"exit_code": 1}
    )
    assert error.command == command
    assert error.error_code == "MGT-CMD-001"
    assert error.error_context.additional_data["command"] == command
    assert error.error_context.additional_data["exit_code"] == 1


def test_environment_error():
    """Test EnvironmentError creation and attributes."""
    env_var = "TEST_VAR"
    error = EnvironmentError(
        "env var missing",
        env_var=env_var,
        severity=ErrorSeverity.WARNING
    )
    assert error.env_var == env_var
    assert error.error_code == "MGT-ENV-001"
    assert error.error_context.additional_data["env_var"] == env_var
    assert error.error_context.severity == ErrorSeverity.WARNING


def test_monitoring_error():
    """Test MonitoringError creation and attributes."""
    metric = "cpu_usage"
    error = MonitoringError(
        "metric unavailable",
        metric=metric,
        retry_config=RetryConfig(max_retries=5, delay_seconds=2)
    )
    assert error.metric == metric
    assert error.error_code == "MGT-MON-001"
    assert error.error_context.additional_data["metric"] == metric
    assert error.error_context.retry_config.max_retries == 5
    assert error.error_context.retry_config.delay_seconds == 2


def test_management_database_error():
    """Test ManagementDatabaseError creation and attributes."""
    db_path = "/path/to/db"
    error = ManagementDatabaseError(
        "db operation failed",
        db_path=db_path,
        additional_data={"operation": "insert"}
    )
    assert error.db_path == db_path
    assert error.error_code == "MGT-DB-001"
    assert error.error_context.additional_data["db_path"] == db_path
    assert error.error_context.additional_data["operation"] == "insert"


@pytest.mark.asyncio
async def test_error_handling_decorator():
    """Test the error handling decorator with various scenarios."""
    
    @with_management_error_handling
    async def successful_function():
        return "success"
    
    @with_management_error_handling
    async def failing_function():
        raise ValueError("test error")
    
    @with_management_error_handling
    async def management_error_function():
        raise ProcessError(
            "process failed",
            pid=1234,
            retry_config=RetryConfig(max_retries=2, delay_seconds=1)
        )

    # Test successful execution
    result = await successful_function()
    assert result == "success"

    # Test handling of non-management errors
    with pytest.raises(ManagementError) as exc_info:
        await failing_function()
    assert exc_info.value.error_code == "MGT-UNEXPECTED-001"
    assert "test error" in str(exc_info.value)
    assert exc_info.value.error_context.additional_data["function"] == "failing_function"
    assert exc_info.value.error_context.source == "management"

    # Test passthrough of management errors
    with pytest.raises(ProcessError) as exc_info:
        await management_error_function()
    assert exc_info.value.error_code == "MGT-PID-001"
    assert exc_info.value.pid == 1234
    assert exc_info.value.error_context.retry_config.max_retries == 2


def test_error_severity_levels():
    """Test error creation with different severity levels."""
    error = ProcessError(
        "warning level error",
        pid=1234,
        severity=ErrorSeverity.WARNING,
        additional_data={"warning_type": "resource"}
    )
    assert error.error_context.severity == ErrorSeverity.WARNING
    assert error.error_context.additional_data["warning_type"] == "resource"

    error = ServerError(
        "critical level error",
        server="test",
        severity=ErrorSeverity.CRITICAL,
        retry_config=RetryConfig(max_retries=1, delay_seconds=5)
    )
    assert error.error_context.severity == ErrorSeverity.CRITICAL
    assert error.error_context.retry_config.max_retries == 1


def test_error_inheritance():
    """Test error class inheritance relationships."""
    error = ProcessError(
        "test error",
        pid=1234,
        additional_data={"test": "data"}
    )
    assert isinstance(error, ProcessError)
    assert isinstance(error, ManagementError)
    assert isinstance(error, Exception)
    assert error.error_context.additional_data["test"] == "data"


def test_error_str_representation():
    """Test string representation of errors."""
    error = ProcessError(
        "test error",
        pid=1234,
        severity=ErrorSeverity.ERROR,
        retry_config=RetryConfig(max_retries=3, delay_seconds=1)
    )
    str_repr = str(error)
    assert "test error" in str_repr
    assert "MGT-PID-001" in str_repr
    assert "ERROR" in str_repr
    assert "pid=1234" in str_repr


def test_error_context_immutability():
    """Test that error context cannot be modified after creation."""
    error = ProcessError(
        "test error",
        pid=1234,
        additional_data={"initial": "value"}
    )
    with pytest.raises(AttributeError):
        error.error_context.additional_data["new_key"] = "value"
    
    # Test that retry config is also immutable
    error = ProcessError(
        "test error",
        pid=1234,
        retry_config=RetryConfig(max_retries=3, delay_seconds=1)
    )
    with pytest.raises(AttributeError):
        error.error_context.retry_config.max_retries = 5


def test_error_context_retry_config():
    """Test error context with retry configuration."""
    error = ProcessError(
        "test error",
        pid=1234,
        retry_config=RetryConfig(
            max_retries=3,
            delay_seconds=1,
            exponential_backoff=True
        )
    )
    assert error.error_context.retry_config.max_retries == 3
    assert error.error_context.retry_config.delay_seconds == 1
    assert error.error_context.retry_config.exponential_backoff is True 