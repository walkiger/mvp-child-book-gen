"""
Comprehensive tests for the error handling framework.

This module tests the unified error handling system including ErrorContext,
standardized error codes, severity levels, and error propagation across all application layers.
"""

import sys
import logging
import sqlite3
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, call
import os
from pathlib import Path
import httpx
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

# Import error handling utilities
from app.core.errors.base import (
    ErrorContext, ErrorSeverity, BaseError, 
    DatabaseError, ValidationError, APIError,
    RetryableError, CriticalError, WarningError,
    ErrorCode, ErrorSource
)
from app.core.errors.api import with_api_error_handling
from app.core.errors.db import with_db_error_handling
from app.core.errors.validation import with_validation_error_handling
from app.core.errors.retry import with_retry
from app.core.utils.datetime import get_utc_now

def test_error_context():
    """Test the ErrorContext functionality."""
    # Test basic context creation
    context = ErrorContext(
        source="test.module",
        operation="test_operation",
        error_code="TEST-OP-001",
        severity=ErrorSeverity.ERROR
    )
    assert context.source == "test.module"
    assert context.operation == "test_operation"
    assert context.error_code == "TEST-OP-001"
    assert context.severity == ErrorSeverity.ERROR
    assert isinstance(context.timestamp, datetime)
    
    # Test context with additional data
    context_with_data = ErrorContext(
        source="test.module",
        operation="test_operation",
        error_code="TEST-OP-002",
        severity=ErrorSeverity.WARNING,
        additional_data={"key": "value"}
    )
    assert context_with_data.additional_data["key"] == "value"
    
    # Test context serialization
    context_dict = context.to_dict()
    assert context_dict["source"] == "test.module"
    assert context_dict["error_code"] == "TEST-OP-001"
    assert "timestamp" in context_dict

def test_validation_error_handling():
    """Test validation error handling with ErrorContext."""
    @with_validation_error_handling
    def validate_user_data(data: dict):
        if not data.get("username"):
            ctx = ErrorContext(
                source="test.validation",
                operation="validate_user",
                error_code="VAL-USER-001",
                severity=ErrorSeverity.ERROR,
                additional_data={"field": "username"}
            )
            raise ValidationError("Username is required", error_context=ctx)
        return data

    # Test validation failure
    with pytest.raises(ValidationError) as exc_info:
        validate_user_data({"email": "test@example.com"})
    
    error = exc_info.value
    assert error.error_context.error_code == "VAL-USER-001"
    assert error.error_context.source == "test.validation"
    assert "Username is required" in str(error)

    # Test successful validation
    result = validate_user_data({"username": "testuser"})
    assert result["username"] == "testuser"

def test_api_error_handling():
    """Test API error handling with ErrorContext."""
    app = FastAPI()
    
    @app.get("/test")
    @with_api_error_handling
    async def test_endpoint():
        ctx = ErrorContext(
            source="test.api",
            operation="get_data",
            error_code="API-TEST-001",
            severity=ErrorSeverity.ERROR
        )
        raise APIError("Failed to get data", error_context=ctx)
    
    client = TestClient(app)
    response = client.get("/test")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "API-TEST-001"
    assert response.json()["error"]["source"] == "test.api"

def test_database_error_handling():
    """Test database error handling with ErrorContext."""
    @with_db_error_handling
    def db_operation():
        ctx = ErrorContext(
            source="test.database",
            operation="insert_data",
            error_code="DB-INS-001",
            severity=ErrorSeverity.ERROR,
            additional_data={"table": "users"}
        )
        raise sqlite3.OperationalError("Database is locked")
    
    with pytest.raises(DatabaseError) as exc_info:
        db_operation()
    
    error = exc_info.value
    assert error.error_context.error_code == "DB-INS-001"
    assert error.error_context.source == "test.database"
    assert "Database is locked" in str(error)

def test_error_severity_handling():
    """Test error severity level handling."""
    for severity in ErrorSeverity:
        ctx = ErrorContext(
            source="test.severity",
            operation="test_severity",
            error_code=f"SEV-TEST-{severity.name}",
            severity=severity
        )
        assert ctx.severity == severity
        assert ctx.to_dict()["severity"] == severity.value

def test_error_propagation():
    """Test error propagation through multiple layers."""
    @with_api_error_handling
    @with_validation_error_handling
    @with_db_error_handling
    def complex_operation(data: dict):
        if not data.get("id"):
            ctx = ErrorContext(
                source="test.complex",
                operation="process_data",
                error_code="PROC-VAL-001",
                severity=ErrorSeverity.ERROR
            )
            raise ValidationError("ID is required", error_context=ctx)
        return data

    with pytest.raises(ValidationError) as exc_info:
        complex_operation({})
    
    error = exc_info.value
    assert error.error_context.error_code == "PROC-VAL-001"
    assert error.error_context.source == "test.complex"
    assert isinstance(error.error_context.timestamp, datetime)

@pytest.mark.anyio
async def test_fastapi_error_handling():
    """Test FastAPI error handling integration."""
    app = FastAPI()
    
    @app.exception_handler(BaseError)
    async def base_error_handler(request: Request, exc: BaseError):
        return JSONResponse(
            status_code=500,
            content={"error": exc.format_message(), "details": exc.details},
        )
    
    @app.get("/test-error")
    async def test_endpoint():
        raise BaseError("Test error", details={"test": "details"})
    
    @app.get("/test-http-error")
    async def test_http_error():
        raise HTTPException(status_code=404, detail="Resource not found")
    
    @app.get("/test-success")
    async def test_success():
        return {"status": "ok"}
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Test BaseError handling
        response = await client.get("/test-error")
        assert response.status_code == 500
        assert response.json() == {
            "error": "ERROR [E-GEN-001]: Test error - {'test': 'details'}",
            "details": {"test": "details"}
        }
        
        # Test HTTPException handling
        response = await client.get("/test-http-error")
        assert response.status_code == 404
        assert response.json()["detail"] == "Resource not found"
        
        # Test successful response
        response = await client.get("/test-success")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

def test_error_context_handling():
    """Test error context handling."""
    # Test with simple context
    error = BaseError("Test message", custom_field=123)
    error_dict = error.to_dict()
    assert error_dict["context"]["custom_field"] == 123
    
    # Test with nested context
    error = BaseError(
        "Test message",
        user={"id": 123, "role": "admin"},
        request={"path": "/api/test", "method": "GET"}
    )
    error_dict = error.to_dict()
    assert error_dict["context"]["user"]["role"] == "admin"
    assert error_dict["context"]["request"]["method"] == "GET"
    
    # Test context merging
    error = BaseError(
        "Test message",
        source="test",
        additional_field="value"
    )
    error_dict = error.to_dict()
    assert error_dict["context"]["source"] == "test"
    assert error_dict["context"]["additional_field"] == "value"

def test_error_context_immutability():
    """Test that ErrorContext is immutable after creation."""
    context = ErrorContext(
        source="test.module",
        operation="test_operation",
        error_code="TEST-OP-001",
        severity=ErrorSeverity.ERROR
    )
    
    # Attempt to modify attributes
    with pytest.raises(AttributeError):
        context.source = "new.source"
    
    with pytest.raises(AttributeError):
        context.error_code = "NEW-CODE"
    
    # Ensure additional_data is immutable
    context.additional_data["new_key"] = "value"
    assert "new_key" not in context.to_dict()["additional_data"]

def test_error_context_inheritance():
    """Test error context inheritance and chaining."""
    parent_context = ErrorContext(
        source="test.parent",
        operation="parent_op",
        error_code="PARENT-001",
        severity=ErrorSeverity.WARNING,
        additional_data={"parent_data": "value"}
    )
    
    child_context = ErrorContext(
        source="test.child",
        operation="child_op",
        error_code="CHILD-001",
        severity=ErrorSeverity.ERROR,
        parent_context=parent_context,
        additional_data={"child_data": "value"}
    )
    
    assert child_context.parent_context == parent_context
    assert "parent_data" in child_context.to_dict()["additional_data"]
    assert child_context.to_dict()["parent_error_code"] == "PARENT-001"

def test_error_code_validation():
    """Test error code format validation."""
    # Valid error code
    context = ErrorContext(
        source="test.module",
        operation="test_operation",
        error_code="TEST-OP-001",
        severity=ErrorSeverity.ERROR
    )
    assert context.error_code == "TEST-OP-001"
    
    # Invalid error code format
    with pytest.raises(ValidationError) as exc_info:
        ErrorContext(
            source="test.module",
            operation="test_operation",
            error_code="invalid_code",
            severity=ErrorSeverity.ERROR
        )
    
    assert "Invalid error code format" in str(exc_info.value)

def test_retryable_error_handling():
    """Test retryable error handling with retry mechanism."""
    retry_count = 0
    
    @with_retry(max_retries=3, delay=0.1)
    def retryable_operation():
        nonlocal retry_count
        retry_count += 1
        
        if retry_count < 3:
            ctx = ErrorContext(
                source="test.retry",
                operation="retry_op",
                error_code="RETRY-001",
                severity=ErrorSeverity.WARNING,
                additional_data={"attempt": retry_count}
            )
            raise RetryableError("Temporary failure", error_context=ctx)
        return "success"
    
    result = retryable_operation()
    assert result == "success"
    assert retry_count == 3

def test_critical_error_handling():
    """Test critical error handling and system state."""
    @with_api_error_handling
    def critical_operation():
        ctx = ErrorContext(
            source="test.critical",
            operation="critical_op",
            error_code="CRIT-001",
            severity=ErrorSeverity.CRITICAL,
            additional_data={"system_state": "unstable"}
        )
        raise CriticalError("Critical system failure", error_context=ctx)
    
    with pytest.raises(CriticalError) as exc_info:
        critical_operation()
    
    error = exc_info.value
    assert error.error_context.severity == ErrorSeverity.CRITICAL
    assert "system_state" in error.error_context.additional_data

def test_warning_error_handling():
    """Test warning error handling and logging."""
    with patch('logging.Logger.warning') as mock_warning:
        @with_api_error_handling
        def warning_operation():
            ctx = ErrorContext(
                source="test.warning",
                operation="warning_op",
                error_code="WARN-001",
                severity=ErrorSeverity.WARNING,
                additional_data={"warning_type": "performance"}
            )
            raise WarningError("Performance degradation", error_context=ctx)
        
        try:
            warning_operation()
        except WarningError as e:
            pass
        
        mock_warning.assert_called_once()
        assert "Performance degradation" in str(mock_warning.call_args)

def test_database_error_handling_sqlalchemy():
    """Test database error handling with SQLAlchemy errors."""
    @with_db_error_handling
    def db_operation():
        ctx = ErrorContext(
            source="test.database",
            operation="insert_data",
            error_code="DB-INS-001",
            severity=ErrorSeverity.ERROR,
            additional_data={"table": "users"}
        )
        raise IntegrityError("statement", "params", "orig")
    
    with pytest.raises(DatabaseError) as exc_info:
        db_operation()
    
    error = exc_info.value
    assert error.error_context.error_code == "DB-INS-001"
    assert error.error_context.source == "test.database"
    assert "Integrity Error" in str(error)

@pytest.mark.asyncio
async def test_async_error_handling():
    """Test asynchronous error handling."""
    app = FastAPI()
    
    @app.get("/async-error")
    @with_api_error_handling
    async def async_error_endpoint():
        ctx = ErrorContext(
            source="test.async",
            operation="async_op",
            error_code="ASYNC-001",
            severity=ErrorSeverity.ERROR,
            additional_data={"async": True}
        )
        raise APIError("Async operation failed", error_context=ctx)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/async-error")
        assert response.status_code == 500
        assert response.json()["error"]["code"] == "ASYNC-001"
        assert response.json()["error"]["source"] == "test.async"
        assert response.json()["error"]["additional_data"]["async"] is True

def test_error_source_validation():
    """Test error source format validation."""
    # Valid source format
    context = ErrorContext(
        source=ErrorSource.DATABASE,
        operation="test_operation",
        error_code=ErrorCode.DATABASE_ERROR,
        severity=ErrorSeverity.ERROR
    )
    assert context.source == ErrorSource.DATABASE
    
    # Invalid source format
    with pytest.raises(ValidationError) as exc_info:
        ErrorContext(
            source="invalid.source.format",
            operation="test_operation",
            error_code=ErrorCode.DATABASE_ERROR,
            severity=ErrorSeverity.ERROR
        )
    
    assert "Invalid error source format" in str(exc_info.value)

def test_error_context_timing():
    """Test error context timing information."""
    start_time = get_utc_now()
    
    context = ErrorContext(
        source="test.timing",
        operation="timing_op",
        error_code="TIME-001",
        severity=ErrorSeverity.ERROR,
        additional_data={"start_time": start_time}
    )
    
    error_dict = context.to_dict()
    assert "timestamp" in error_dict
    assert "duration" in error_dict
    
    # Ensure timestamp is after start_time
    assert datetime.fromisoformat(error_dict["timestamp"]) > start_time

if __name__ == "__main__":
    pytest.main(["-v", __file__]) 