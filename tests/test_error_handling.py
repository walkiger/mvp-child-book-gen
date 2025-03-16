"""
Comprehensive tests for the error handling framework.

Note: This project uses standard-crypt (installed via pip) as a replacement for Python's
built-in crypt module, which is deprecated in Python 3.11 and will be removed in 3.13.
This is to address the deprecation warning from passlib, which currently depends on
the crypt module. standard-crypt is a pure Python, platform-independent implementation
that serves as a drop-in replacement.
"""

import sys
import logging
import sqlite3
import pytest
from unittest.mock import MagicMock, patch, call
import os
from pathlib import Path
import httpx
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.testclient import TestClient
from httpx import AsyncClient, ASGITransport

# Import error handling utilities
from utils.error_handling import (
    BaseError, ServerError, DatabaseError, ConfigError, 
    ResourceError, InputError, ImageError, ErrorSeverity,
    handle_error, setup_logger, with_error_handling, with_retry,
    CircuitBreaker, CircuitState
)
from management.errors import ProcessError, db_error_handler


def test_base_error_class():
    """Test the base BaseError class."""
    # Test basic error creation
    error = BaseError("Test error message")
    assert "ERROR [E-GEN-001]: Test error message" in str(error)
    assert error.severity == ErrorSeverity.ERROR
    assert error.http_status_code == 500
    
    # Test with custom attributes
    error = BaseError(
        "Test error message",
        severity=ErrorSeverity.WARNING,
        error_code="E-TEST-001",
        http_status_code=400,
        details="Additional details",
        custom_field="Custom value"
    )
    assert "WARNING [E-TEST-001]: Test error message - Additional details" in str(error)
    assert error.severity == ErrorSeverity.WARNING
    assert error.http_status_code == 400
    assert error.kwargs["custom_field"] == "Custom value"
    
    # Test dictionary conversion
    error_dict = error.to_dict()
    assert error_dict["error_code"] == "E-TEST-001"
    assert error_dict["severity"] == "WARNING"
    assert error_dict["message"] == "Test error message"
    assert error_dict["details"] == "Additional details"
    assert error_dict["context"]["custom_field"] == "Custom value"

    # Test error inheritance
    class CustomError(BaseError):
        def __init__(self, message, **kwargs):
            super().__init__(message, error_code="E-CUSTOM-001", **kwargs)
    
    custom_error = CustomError("Custom error")
    assert "ERROR [E-CUSTOM-001]" in str(custom_error)


def test_database_error_formatting():
    """Test DatabaseError message formatting."""
    # Test basic database error
    error = DatabaseError("Database connection failed")
    assert str(error) == "Database connection failed"
    
    # Test with db_path
    error = DatabaseError("Database connection failed", db_path="/path/to/db.sqlite")
    assert str(error) == "Database connection failed"
    assert error.db_path == "/path/to/db.sqlite"
    
    # Test with additional kwargs
    error = DatabaseError(
        "Database connection failed",
        db_path="/path/to/db.sqlite",
        error_code="E-DB-TEST",
        details="Connection timeout"
    )
    assert str(error) == "Database connection failed"
    assert error.error_code == "E-DB-TEST"

    # Test with error details
    error = DatabaseError("Permission denied", details="File is read-only")
    assert str(error) == "Permission denied"
    assert error.details == "File is read-only"


def test_db_error_handler():
    """Test database error handler decorator."""
    @db_error_handler
    def db_operation(db_path):
        raise sqlite3.OperationalError("database is locked")
    
    with pytest.raises(DatabaseError) as exc_info:
        db_operation("test.db")
    assert str(exc_info.value) == "Database is locked"
    
    @db_error_handler
    def db_operation_integrity(db_path):
        raise sqlite3.IntegrityError("UNIQUE constraint failed")
    
    with pytest.raises(DatabaseError) as exc_info:
        db_operation_integrity("test.db")
    assert str(exc_info.value) == "Integrity error"
    
    @db_error_handler
    def db_operation_corrupt(db_path):
        raise sqlite3.DatabaseError("file is not a database")
    
    with pytest.raises(DatabaseError) as exc_info:
        db_operation_corrupt("test.db")
    assert str(exc_info.value) == "Database is corrupted"

    # Test successful operation
    @db_error_handler
    def successful_operation(db_path):
        return "success"
    
    result = successful_operation("test.db")
    assert result == "success"


def test_error_handling_decorator():
    """Test the with_error_handling decorator."""
    mock_logger = MagicMock()
    
    with patch('utils.error_handling.setup_logger', return_value=mock_logger):
        # Test handling of BaseError
        @with_error_handling(logger_name="test")
        def raise_base_error():
            raise BaseError("Test error", severity=ErrorSeverity.WARNING)
        
        with pytest.raises(BaseError):
            raise_base_error()
        mock_logger.warning.assert_called_once()
        
        # Test handling of FileNotFoundError
        mock_logger.reset_mock()
        @with_error_handling(logger_name="test")
        def raise_file_error():
            raise FileNotFoundError("test.txt not found")
        
        with pytest.raises(ResourceError):
            raise_file_error()
        mock_logger.error.assert_called_once()
        
        # Test handling of generic exception
        mock_logger.reset_mock()
        @with_error_handling(logger_name="test", context="TestContext")
        def raise_generic_error():
            raise ValueError("Test value error")
        
        with pytest.raises(BaseError):
            raise_generic_error()
        mock_logger.error.assert_called_once()
        assert "TestContext" in str(mock_logger.error.call_args[0][0])

        # Test successful execution
        mock_logger.reset_mock()
        @with_error_handling(logger_name="test")
        def successful_operation():
            return "success"
        
        result = successful_operation()
        assert result == "success"
        assert not mock_logger.error.called


def test_retry_decorator():
    """Test the with_retry decorator."""
    mock_logger = MagicMock()
    attempts = []
    
    with patch('utils.error_handling.setup_logger', return_value=mock_logger):
        @with_retry(max_attempts=3, retry_delay=0.1)
        def failing_function():
            attempts.append(1)
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            failing_function()
        
        assert len(attempts) == 3  # Should have tried 3 times
        assert mock_logger.warning.call_count == 2  # Should have logged 2 retries

        # Test successful retry
        mock_logger.reset_mock()
        success_attempts = []
        
        @with_retry(max_attempts=3, retry_delay=0.1)
        def eventually_succeeds():
            success_attempts.append(1)
            if len(success_attempts) < 2:
                raise ValueError("Temporary error")
            return "success"
        
        result = eventually_succeeds()
        assert result == "success"
        assert len(success_attempts) == 2  # Should succeed on second attempt
        assert mock_logger.warning.call_count == 1  # Should have logged 1 retry


def test_circuit_breaker():
    """Test the CircuitBreaker implementation."""
    breaker = CircuitBreaker("test_service", failure_threshold=2, reset_timeout=0.1)
    
    @breaker
    def service_call():
        raise ServerError("Service unavailable")
    
    # First call - should fail normally
    with pytest.raises(ServerError):
        service_call()
    assert breaker.state == CircuitState.CLOSED
    
    # Second call - should open the circuit
    with pytest.raises(ServerError):
        service_call()
    assert breaker.state == CircuitState.OPEN
    
    # Third call - should fail fast with circuit open
    with pytest.raises(ServerError) as exc_info:
        service_call()
    assert "Circuit for test_service is open" in str(exc_info.value)
    
    # Wait for reset timeout
    import time
    time.sleep(0.2)
    
    # Next call should be in HALF_OPEN state
    with pytest.raises(ServerError):
        service_call()
    assert breaker.state == CircuitState.HALF_OPEN

    # Test successful recovery
    breaker = CircuitBreaker("recovery_test", failure_threshold=2, reset_timeout=0.1)
    
    @breaker
    def recovering_service():
        if breaker.failure_count < 2:
            raise ServerError("Temporary failure")
        return "success"
    
    # First call - should fail
    with pytest.raises(ServerError):
        recovering_service()
    
    # Second call - should fail and open circuit
    with pytest.raises(ServerError):
        recovering_service()
    assert breaker.state == CircuitState.OPEN
    
    # Wait for reset
    time.sleep(0.2)
    
    # Should succeed and close circuit
    result = recovering_service()
    assert result == "success"
    assert breaker.state == CircuitState.CLOSED


def test_error_handler_integration():
    """Test integration of different error handling components."""
    mock_logger = MagicMock()
    
    with patch('utils.error_handling.setup_logger', return_value=mock_logger):
        @with_retry(max_attempts=2, retry_delay=0.1)
        @with_error_handling(logger_name="test")
        @db_error_handler
        def complex_operation(db_path):
            raise sqlite3.OperationalError("database is locked")
        
        with pytest.raises(DatabaseError) as exc_info:
            complex_operation("test.db")
        
        assert str(exc_info.value) == "Database is locked"
        assert mock_logger.error.call_count >= 1

        # Test successful integration
        @with_retry(max_attempts=2)
        @with_error_handling(logger_name="test")
        @db_error_handler
        def successful_complex_operation(db_path):
            return "success"
        
        result = successful_complex_operation("test.db")
        assert result == "success"


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


def test_error_severity_levels():
    """Test error severity level handling."""
    # Test INFO severity
    info_error = BaseError("Info message", severity=ErrorSeverity.INFO)
    assert "INFO" in str(info_error)
    assert info_error.severity == ErrorSeverity.INFO
    
    # Test WARNING severity
    warning_error = BaseError("Warning message", severity=ErrorSeverity.WARNING)
    assert "WARNING" in str(warning_error)
    assert warning_error.severity == ErrorSeverity.WARNING
    
    # Test ERROR severity
    error = BaseError("Error message", severity=ErrorSeverity.ERROR)
    assert "ERROR" in str(error)
    assert error.severity == ErrorSeverity.ERROR
    
    # Test CRITICAL severity
    critical_error = BaseError("Critical message", severity=ErrorSeverity.CRITICAL)
    assert "CRITICAL" in str(critical_error)
    assert critical_error.severity == ErrorSeverity.CRITICAL


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


if __name__ == "__main__":
    pytest.main(["-v", __file__]) 