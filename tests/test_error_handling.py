"""
Comprehensive tests for the error handling framework.
"""

import sys
import logging
import pytest
from unittest.mock import MagicMock, patch, call

# Import error handling utilities
from utils.error_handling import (
    BaseError, ServerError, DatabaseError, ConfigError, 
    ResourceError, InputError, ImageError, ErrorSeverity,
    handle_error, setup_logger, with_error_handling
)
from management.errors import ProcessError


def test_base_error_class():
    """Test the base BaseError class."""
    
    error = BaseError("Test error message")
    assert "ERROR [E-GEN-001]: Test error message" in str(error)
    assert error.severity == ErrorSeverity.ERROR  # Default severity
    
    # Test with custom severity and context
    error = BaseError(
        "Test error message",
        severity=ErrorSeverity.WARNING,
        error_code="E-TEST-001"
    )
    assert "WARNING [E-TEST-001]: Test error message" in str(error)
    assert error.severity == ErrorSeverity.WARNING


def test_error_inheritance():
    """Test that all error types inherit from BaseError."""
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
    
    # Each should have its own type
    assert type(server_error) is ServerError
    assert type(process_error) is ProcessError
    assert type(db_error) is DatabaseError
    assert type(config_error) is ConfigError


def test_error_severity_levels():
    """Test that error severity levels work correctly."""
    info_error = BaseError("Info message", severity=ErrorSeverity.INFO)
    warning_error = BaseError("Warning message", severity=ErrorSeverity.WARNING)
    error_error = BaseError("Error message", severity=ErrorSeverity.ERROR)
    critical_error = BaseError("Critical message", severity=ErrorSeverity.CRITICAL)
    
    assert "INFO [" in str(info_error)
    assert "WARNING [" in str(warning_error)
    assert "ERROR [" in str(error_error)
    assert "CRITICAL [" in str(critical_error)


def test_error_details():
    """Test that error details are included correctly."""
    # Error with details
    error = BaseError("Error message", details="Additional details")
    assert "ERROR [E-GEN-001]: Error message - Additional details" in str(error)
    assert error.details == "Additional details"
    
    # Error with context and details
    error = BaseError(
        "Error message", 
        details="Additional details",
        error_code="E-TEST-001"
    )
    assert "ERROR [E-TEST-001]: Error message - Additional details" in str(error)
    assert error.details == "Additional details"


def test_decorator_basic():
    """Test the basic functionality of the error handling decorator."""
    mock_logger = MagicMock()
    
    with patch('utils.error_handling.setup_logger', return_value=mock_logger):
        # Define a function that raises an exception
        @with_error_handling(logger_name="test")
        def failing_function():
            raise ValueError("Test error")
            return True
        
        # Call the function and check the result
        result = failing_function()
        assert result is False  # Should return False when exception is caught
        
        # Check that the logger was called
        mock_logger.error.assert_called_once()
        assert "Test error" in mock_logger.error.call_args[0][0]


def test_decorator_management_error():
    """Test that decorator handles BaseError correctly."""
    mock_logger = MagicMock()
    
    with patch('utils.error_handling.setup_logger', return_value=mock_logger):
        # Define a function that raises a BaseError
        @with_error_handling(logger_name="test")
        def failing_function():
            raise BaseError("Test error", severity=ErrorSeverity.WARNING)
            return True
        
        # Call the function and check the result
        result = failing_function()
        assert result is False  # Should return False when exception is caught
        
        # Check that the logger was called with the right level
        mock_logger.warning.assert_called_once()
        assert "Test error" in mock_logger.warning.call_args[0][0]


def test_decorator_no_error():
    """Test that decorator passes through return value when no error occurs."""
    mock_logger = MagicMock()
    
    with patch('utils.error_handling.setup_logger', return_value=mock_logger):
        # Define a function that doesn't raise an exception
        @with_error_handling(logger_name="test")
        def successful_function():
            return "success"
        
        # Call the function and check the result
        result = successful_function()
        assert result == "success"  # Should return the original return value
        
        # Check that the logger was not called
        mock_logger.error.assert_not_called()
        mock_logger.warning.assert_not_called()
        mock_logger.info.assert_not_called()


def test_decorator_exit_behavior():
    """Test that exit_on_error parameter works correctly."""
    mock_logger = MagicMock()
    mock_handle_error = MagicMock()
    
    with patch('utils.error_handling.handle_error', mock_handle_error):
        with patch('utils.error_handling.setup_logger', return_value=mock_logger):
            # Define a function with exit_on_error=True
            @with_error_handling(exit_on_error=True, logger_name="test")
            def failing_function():
                raise ValueError("Test error")
                return True
            
            # Call the function
            result = failing_function()
            assert result is False
            
            # Check that handle_error was called with exit_app=True
            mock_handle_error.assert_called_once()
            # Check that the third positional argument is True (exit_app)
            args, _ = mock_handle_error.call_args
            assert len(args) >= 3
            assert args[2] is True


def test_handle_error_severity():
    """Test that handle_error respects error severity."""
    mock_logger = MagicMock()
    
    # Test with BaseError instances of different severity
    info_error = BaseError("Info test", severity=ErrorSeverity.INFO)
    warning_error = BaseError("Warning test", severity=ErrorSeverity.WARNING)
    error_error = BaseError("Error test", severity=ErrorSeverity.ERROR)
    
    # Call handle_error with each error
    handle_error(info_error, mock_logger)
    handle_error(warning_error, mock_logger)
    handle_error(error_error, mock_logger)
    
    # Check that the logger was called with the right level
    mock_logger.info.assert_called_once()
    mock_logger.warning.assert_called_once()
    mock_logger.error.assert_called_once()
    
    # Check the messages
    assert "Info test" in mock_logger.info.call_args[0][0]
    assert "Warning test" in mock_logger.warning.call_args[0][0]
    assert "Error test" in mock_logger.error.call_args[0][0]


def test_handle_error_exit():
    """Test that handle_error exits when requested."""
    mock_logger = MagicMock()
    mock_exit = MagicMock()
    
    with patch('sys.exit', mock_exit):
        # Call handle_error with exit_app=True
        handle_error(BaseError("Test error"), mock_logger, exit_app=True)
        
        # Check that sys.exit was called
        mock_exit.assert_called_once()


def test_handle_error_generic_exception():
    """Test handle_error with a non-BaseError exception."""
    mock_logger = MagicMock()
    
    # Call handle_error with a generic exception
    with patch('traceback.format_exc', return_value="Test traceback"):
        handle_error(ValueError("Test error"), mock_logger)
    
    # Should convert to BaseError
    mock_logger.error.assert_called_once()
    assert "Test error" in mock_logger.error.call_args[0][0]


def test_setup_logger():
    """Test that setup_logger creates a properly configured logger."""
    # Create a logger
    logger = setup_logger("test_logger")
    
    # Check that it has the right name
    assert logger.name == "test_logger"
    
    # Check that it has at least one handler
    assert len(logger.handlers) > 0
    
    # Check that the level is set
    assert logger.level == logging.INFO


def test_decorator_preserves_function_metadata():
    """Test that the decorator preserves function metadata."""
    @with_error_handling
    def test_function(arg1, arg2):
        """Test function docstring."""
        return arg1 + arg2
    
    # Check that the function name and docstring are preserved
    assert test_function.__name__ == "test_function"
    assert test_function.__doc__ == "Test function docstring."
    
    # Check that the function still works
    assert test_function(1, 2) == 3


def test_error_handler_calls():
    """Test that the error handler is called with the right arguments."""
    mock_handle_error = MagicMock()
    mock_logger = MagicMock()
    
    with patch('utils.error_handling.handle_error', mock_handle_error):
        with patch('utils.error_handling.setup_logger', return_value=mock_logger):
            # Define a function that raises different types of errors
            @with_error_handling(logger_name="test")
            def test_function(error_type):
                if error_type == "value":
                    raise ValueError("Test ValueError")
                elif error_type == "base":
                    raise BaseError("Test BaseError")
                elif error_type == "server":
                    raise ServerError("Test ServerError")
                return True
            
            # Call with ValueError
            test_function("value")
            # First call should have a BaseError (converted from ValueError)
            args, _ = mock_handle_error.call_args_list[0]
            error_arg = args[0]
            assert isinstance(error_arg, BaseError)
            assert "Test ValueError" in str(error_arg)
            
            # Call with BaseError
            test_function("base")
            # Second call should have a BaseError
            args, _ = mock_handle_error.call_args_list[1]
            error_arg = args[0]
            assert isinstance(error_arg, BaseError)
            assert "Test BaseError" in str(error_arg)
            
            # Call with ServerError
            test_function("server")
            # Third call should have a ServerError
            args, _ = mock_handle_error.call_args_list[2]
            error_arg = args[0]
            assert isinstance(error_arg, ServerError)
            assert "Test ServerError" in str(error_arg)


if __name__ == "__main__":
    pytest.main(["-v", __file__]) 