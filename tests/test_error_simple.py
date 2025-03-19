"""
Simple tests for unified error handling framework.

Tests basic functionality of the ErrorContext-based error handling system
including error creation, validation, formatting, and error chains.
"""

import sys
import pytest
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from app.core.errors.base import (
    ErrorContext, ErrorSeverity, BaseError,
    ValidationError, DatabaseError, APIError,
    ProcessError, ResourceError, RetryableError,
    CriticalError, WarningError, ErrorCode,
    ErrorSource, ErrorFormatter
)
from app.core.errors.api import with_api_error_handling
from app.core.errors.validation import with_validation_error_handling
from app.core.errors.db import with_db_error_handling
from app.core.errors.retry import with_retry
from app.core.utils.datetime import get_utc_now


def test_error_context_basics():
    """Test basic ErrorContext functionality."""
    # Create contexts for different error types
    api_context = ErrorContext(
        source="test.api",
        operation="test_operation",
        error_code="API-TEST-001",
        severity=ErrorSeverity.ERROR
    )
    
    validation_context = ErrorContext(
        source="test.validation",
        operation="validate_data",
        error_code="VAL-TEST-001",
        severity=ErrorSeverity.WARNING
    )
    
    db_context = ErrorContext(
        source="test.database",
        operation="db_operation",
        error_code="DB-TEST-001",
        severity=ErrorSeverity.CRITICAL
    )
    
    # Verify context attributes
    assert api_context.source == "test.api"
    assert validation_context.operation == "validate_data"
    assert db_context.error_code == "DB-TEST-001"
    
    # Verify timestamps are datetime objects
    assert isinstance(api_context.timestamp, datetime)
    assert isinstance(validation_context.timestamp, datetime)
    assert isinstance(db_context.timestamp, datetime)


def test_error_severity_levels():
    """Test error severity levels with ErrorContext."""
    # Create contexts with different severity levels
    info_ctx = ErrorContext(
        source="test.severity",
        operation="info_op",
        error_code="SEV-INFO-001",
        severity=ErrorSeverity.INFO
    )
    
    warning_ctx = ErrorContext(
        source="test.severity",
        operation="warning_op",
        error_code="SEV-WARN-001",
        severity=ErrorSeverity.WARNING
    )
    
    error_ctx = ErrorContext(
        source="test.severity",
        operation="error_op",
        error_code="SEV-ERR-001",
        severity=ErrorSeverity.ERROR
    )
    
    critical_ctx = ErrorContext(
        source="test.severity",
        operation="critical_op",
        error_code="SEV-CRIT-001",
        severity=ErrorSeverity.CRITICAL
    )
    
    # Create errors with contexts
    info_error = ValidationError("Info message", error_context=info_ctx)
    warning_error = ValidationError("Warning message", error_context=warning_ctx)
    error_error = ValidationError("Error message", error_context=error_ctx)
    critical_error = ValidationError("Critical message", error_context=critical_ctx)
    
    # Verify severity levels
    assert info_error.error_context.severity == ErrorSeverity.INFO
    assert warning_error.error_context.severity == ErrorSeverity.WARNING
    assert error_error.error_context.severity == ErrorSeverity.ERROR
    assert critical_error.error_context.severity == ErrorSeverity.CRITICAL


def test_error_context_data():
    """Test error context with additional data."""
    # Create context with additional data
    context = ErrorContext(
        source="test.data",
        operation="data_operation",
        error_code="DATA-TEST-001",
        severity=ErrorSeverity.ERROR,
        additional_data={
            "user_id": 123,
            "action": "test",
            "metadata": {
                "version": "1.0",
                "environment": "test"
            }
        }
    )
    
    # Create error with context
    error = ValidationError("Test error", error_context=context)
    
    # Verify context data
    assert error.error_context.additional_data["user_id"] == 123
    assert error.error_context.additional_data["action"] == "test"
    assert error.error_context.additional_data["metadata"]["version"] == "1.0"
    
    # Test serialization
    error_dict = error.to_dict()
    assert error_dict["error_context"]["additional_data"]["user_id"] == 123
    assert error_dict["error_context"]["source"] == "test.data"
    assert error_dict["error_context"]["error_code"] == "DATA-TEST-001"


def test_error_handling_decorator():
    """Test error handling decorators."""
    @with_api_error_handling
    def api_function():
        ctx = ErrorContext(
            source="test.api",
            operation="test_api",
            error_code="API-TEST-001",
            severity=ErrorSeverity.ERROR
        )
        raise APIError("API error", error_context=ctx)
    
    @with_validation_error_handling
    def validation_function():
        ctx = ErrorContext(
            source="test.validation",
            operation="test_validation",
            error_code="VAL-TEST-001",
            severity=ErrorSeverity.ERROR
        )
        raise ValidationError("Validation error", error_context=ctx)
    
    @with_db_error_handling
    def db_function():
        ctx = ErrorContext(
            source="test.database",
            operation="test_db",
            error_code="DB-TEST-001",
            severity=ErrorSeverity.ERROR
        )
        raise DatabaseError("Database error", error_context=ctx)
    
    # Test API error handling
    with pytest.raises(APIError) as exc_info:
        api_function()
    assert exc_info.value.error_context.error_code == "API-TEST-001"
    
    # Test validation error handling
    with pytest.raises(ValidationError) as exc_info:
        validation_function()
    assert exc_info.value.error_context.error_code == "VAL-TEST-001"
    
    # Test database error handling
    with pytest.raises(DatabaseError) as exc_info:
        db_function()
    assert exc_info.value.error_context.error_code == "DB-TEST-001"


def test_error_chaining():
    """Test error chaining with ErrorContext."""
    try:
        try:
            try:
                ctx = ErrorContext(
                    source="test.validation",
                    operation="validate_input",
                    error_code="VAL-CHAIN-001",
                    severity=ErrorSeverity.ERROR
                )
                raise ValidationError("Invalid input", error_context=ctx)
            except ValidationError as e:
                ctx = ErrorContext(
                    source="test.api",
                    operation="process_input",
                    error_code="API-CHAIN-001",
                    severity=ErrorSeverity.ERROR
                )
                raise APIError("API processing failed", error_context=ctx) from e
        except APIError as e:
            ctx = ErrorContext(
                source="test.database",
                operation="save_data",
                error_code="DB-CHAIN-001",
                severity=ErrorSeverity.ERROR
            )
            raise DatabaseError("Database operation failed", error_context=ctx) from e
    except DatabaseError as e:
        # Check error chain
        assert isinstance(e.__cause__, APIError)
        assert isinstance(e.__cause__.__cause__, ValidationError)
        assert e.error_context.error_code == "DB-CHAIN-001"
        assert e.__cause__.error_context.error_code == "API-CHAIN-001"
        assert e.__cause__.__cause__.error_context.error_code == "VAL-CHAIN-001"


def test_error_context_validation():
    """Test error context validation rules."""
    # Test valid error context
    valid_context = ErrorContext(
        source="test.validation",
        operation="test_operation",
        error_code="TEST-VAL-001",
        severity=ErrorSeverity.ERROR
    )
    assert valid_context.error_code == "TEST-VAL-001"
    
    # Test invalid source format
    with pytest.raises(ValidationError) as exc_info:
        ErrorContext(
            source="invalid source",
            operation="test_operation",
            error_code="TEST-VAL-001",
            severity=ErrorSeverity.ERROR
        )
    assert "Invalid source format" in str(exc_info.value)
    
    # Test invalid error code format
    with pytest.raises(ValidationError) as exc_info:
        ErrorContext(
            source="test.validation",
            operation="test_operation",
            error_code="invalid_code",
            severity=ErrorSeverity.ERROR
        )
    assert "Invalid error code format" in str(exc_info.value)
    
    # Test invalid operation name
    with pytest.raises(ValidationError) as exc_info:
        ErrorContext(
            source="test.validation",
            operation="",  # Empty operation name
            error_code="TEST-VAL-001",
            severity=ErrorSeverity.ERROR
        )
    assert "Invalid operation name" in str(exc_info.value)


def test_error_context_immutability():
    """Test error context immutability."""
    context = ErrorContext(
        source="test.immutable",
        operation="test_operation",
        error_code="TEST-IMM-001",
        severity=ErrorSeverity.ERROR,
        additional_data={"key": "value"}
    )
    
    # Test immutability of basic attributes
    with pytest.raises(AttributeError):
        context.source = "new.source"
    
    with pytest.raises(AttributeError):
        context.error_code = "NEW-CODE"
    
    with pytest.raises(AttributeError):
        context.severity = ErrorSeverity.WARNING
    
    # Test immutability of additional data
    original_data = context.additional_data.copy()
    context.additional_data["new_key"] = "new_value"
    assert context.additional_data == original_data


def test_error_formatting():
    """Test error message formatting."""
    context = ErrorContext(
        source="test.formatting",
        operation="format_test",
        error_code="TEST-FMT-001",
        severity=ErrorSeverity.ERROR,
        additional_data={
            "user_id": 123,
            "action": "test",
            "details": {
                "field": "username",
                "value": "invalid"
            }
        }
    )
    
    error = ValidationError("Validation failed", error_context=context)
    
    # Test default formatting
    default_format = str(error)
    assert "TEST-FMT-001" in default_format
    assert "Validation failed" in default_format
    assert "test.formatting" in default_format
    
    # Test custom formatting
    custom_format = error.format_message(
        template="{severity}: [{code}] {message} in {source} - {details}"
    )
    assert "ERROR: [TEST-FMT-001]" in custom_format
    assert "Validation failed" in custom_format
    assert "test.formatting" in custom_format
    
    # Test JSON formatting
    json_format = error.to_dict()
    assert json_format["error_context"]["error_code"] == "TEST-FMT-001"
    assert json_format["error_context"]["additional_data"]["user_id"] == 123
    assert json_format["message"] == "Validation failed"


def test_error_inheritance():
    """Test error class inheritance and type checking."""
    # Create different types of errors
    validation_error = ValidationError(
        "Validation error",
        error_context=ErrorContext(
            source="test.inheritance",
            operation="validate",
            error_code="TEST-INH-001",
            severity=ErrorSeverity.ERROR
        )
    )
    
    db_error = DatabaseError(
        "Database error",
        error_context=ErrorContext(
            source="test.inheritance",
            operation="db_operation",
            error_code="TEST-INH-002",
            severity=ErrorSeverity.ERROR
        )
    )
    
    api_error = APIError(
        "API error",
        error_context=ErrorContext(
            source="test.inheritance",
            operation="api_call",
            error_code="TEST-INH-003",
            severity=ErrorSeverity.ERROR
        )
    )
    
    # Test inheritance relationships
    assert isinstance(validation_error, BaseError)
    assert isinstance(db_error, BaseError)
    assert isinstance(api_error, BaseError)
    
    # Test specific error types
    assert isinstance(validation_error, ValidationError)
    assert not isinstance(validation_error, DatabaseError)
    assert not isinstance(validation_error, APIError)
    
    # Test error context inheritance
    assert validation_error.error_context.error_code.startswith("TEST-INH")
    assert db_error.error_context.error_code.startswith("TEST-INH")
    assert api_error.error_context.error_code.startswith("TEST-INH")


def test_retryable_error():
    """Test retryable error handling."""
    retry_count = 0
    
    @with_retry(max_retries=3, delay=0.1)
    def retryable_operation():
        nonlocal retry_count
        retry_count += 1
        
        if retry_count < 3:
            raise RetryableError(
                "Temporary failure",
                error_context=ErrorContext(
                    source="test.retry",
                    operation="retry_test",
                    error_code="TEST-RETRY-001",
                    severity=ErrorSeverity.WARNING,
                    additional_data={"attempt": retry_count}
                )
            )
        return "success"
    
    # Test successful retry
    result = retryable_operation()
    assert result == "success"
    assert retry_count == 3
    
    # Test max retries exceeded
    retry_count = 0
    @with_retry(max_retries=2, delay=0.1)
    def failing_operation():
        nonlocal retry_count
        retry_count += 1
        raise RetryableError(
            "Always fails",
            error_context=ErrorContext(
                source="test.retry",
                operation="failing_test",
                error_code="TEST-RETRY-002",
                severity=ErrorSeverity.ERROR,
                additional_data={"attempt": retry_count}
            )
        )
    
    with pytest.raises(RetryableError) as exc_info:
        failing_operation()
    assert retry_count == 2
    assert exc_info.value.error_context.additional_data["attempt"] == 2


def test_error_context_timing():
    """Test error context timing information."""
    start_time = get_utc_now()
    
    # Create error with timing information
    context = ErrorContext(
        source="test.timing",
        operation="timing_test",
        error_code="TEST-TIME-001",
        severity=ErrorSeverity.ERROR,
        additional_data={"start_time": start_time}
    )
    
    error = APIError("Timing test", error_context=context)
    error_dict = error.to_dict()
    
    # Verify timing information
    assert "timestamp" in error_dict["error_context"]
    error_time = datetime.fromisoformat(error_dict["error_context"]["timestamp"])
    assert error_time > start_time
    assert error_time - start_time < timedelta(seconds=1)


def test_error_context_nesting():
    """Test nested error contexts."""
    # Create parent context
    parent_context = ErrorContext(
        source="test.parent",
        operation="parent_operation",
        error_code="TEST-NEST-001",
        severity=ErrorSeverity.WARNING,
        additional_data={"parent_data": "value"}
    )
    
    # Create child context with parent
    child_context = ErrorContext(
        source="test.child",
        operation="child_operation",
        error_code="TEST-NEST-002",
        severity=ErrorSeverity.ERROR,
        parent_context=parent_context,
        additional_data={"child_data": "value"}
    )
    
    # Create error with nested context
    error = ValidationError("Nested error", error_context=child_context)
    error_dict = error.to_dict()
    
    # Verify nested context information
    assert error_dict["error_context"]["error_code"] == "TEST-NEST-002"
    assert error_dict["error_context"]["parent_error_code"] == "TEST-NEST-001"
    assert "parent_data" in error_dict["error_context"]["additional_data"]
    assert "child_data" in error_dict["error_context"]["additional_data"]


if __name__ == "__main__":
    pytest.main(["-v", __file__]) 