"""
Simple tests for error handling framework without mocking.
"""

import sys
import pytest

# Import error handling utilities
from utils.error_handling import (
    BaseError, ServerError, DatabaseError, ConfigError, 
    ResourceError, InputError, ImageError, ErrorSeverity,
    with_error_handling
)
from management.errors import ProcessError


def test_error_class_hierarchy():
    """Test error class hierarchy."""
    # Create instances of each error type
    base_error = BaseError("Base error")
    server_error = ServerError("Server error")
    process_error = ProcessError("Process error")
    db_error = DatabaseError("Database error")
    config_error = ConfigError("Config error")
    resource_error = ResourceError("Resource error")
    input_error = InputError("Input error")
    image_error = ImageError("Image error")
    
    # All should be instances of BaseError
    assert isinstance(server_error, BaseError)
    assert isinstance(process_error, BaseError)
    assert isinstance(db_error, BaseError)
    assert isinstance(config_error, BaseError)
    assert isinstance(resource_error, BaseError)
    assert isinstance(input_error, BaseError)
    assert isinstance(image_error, BaseError)


def test_error_severity():
    """Test error severity levels."""
    # Create errors with different severity levels
    info = BaseError("Info message", severity=ErrorSeverity.INFO)
    warning = BaseError("Warning message", severity=ErrorSeverity.WARNING)
    error = BaseError("Error message", severity=ErrorSeverity.ERROR)
    critical = BaseError("Critical message", severity=ErrorSeverity.CRITICAL)
    
    # Check string representation
    assert "INFO [" in str(info)
    assert "WARNING [" in str(warning)
    assert "ERROR [" in str(error)
    assert "CRITICAL [" in str(critical)


def test_error_details():
    """Test error details."""
    # Create error with details
    error = BaseError("Error with details", details="Some details")
    
    # Check that details are included
    assert error.details == "Some details"


def test_decorator_basic():
    """Test basic decorator functionality."""
    # Define a function that raises an exception
    @with_error_handling
    def failing_function():
        raise BaseError("Test management error")
        return True
    
    # Call the function
    result = failing_function()
    
    # Should return False when exception is caught
    assert result is False


if __name__ == "__main__":
    pytest.main(["-v", __file__]) 