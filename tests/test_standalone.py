"""
Standalone tests for error handling utilities.

This file contains tests that can be run independently to verify
the error handling framework functionality with visual feedback.
"""

import sys
import logging
from enum import Enum

# Import error handling utilities
from utils.error_handling import (
    BaseError, ServerError, DatabaseError, ConfigError, 
    ResourceError, InputError, ImageError, ErrorSeverity,
    handle_error, setup_logger
)
from management.errors import ProcessError


def test_error_classes():
    """Test error classes with visual feedback."""
    print("\n=== Testing Error Classes ===")
    
    # Test with BaseError
    error = BaseError("Test base error")
    print(f"BaseError: {error}")
    
    # Test with ServerError
    error = ServerError("Test server error")
    print(f"ServerError: {error}")
    
    # Test with ProcessError
    error = ProcessError("Test process error", pid=12345)
    print(f"ProcessError: {error}")
    
    # Test with DatabaseError
    error = DatabaseError("Test database error", db_path="test.db")
    print(f"DatabaseError: {error}")
    
    print("✓ Error classes test completed")


def test_severity_levels():
    """Test error severity levels with visual feedback."""
    print("\n=== Testing Error Severity Levels ===")
    
    # Test all severity levels
    for severity in ErrorSeverity:
        error = BaseError("Test severity", severity=severity)
        print(f"{severity.name}: {error}")
    
    print("✓ Severity levels test completed")


def test_error_formatting():
    """Test error message formatting with visual feedback."""
    print("\n=== Testing Error Formatting ===")
    
    # Basic error
    base_error = BaseError("Base error message")
    print(f"Basic error: {base_error}")
    
    # Error with context
    context_error = BaseError("Error with context", context="test_function")
    print(f"Error with context: {context_error}")
    
    # Error with details
    detailed_error = BaseError("Error with details", details="Additional info")
    print(f"Error with details: {detailed_error}")
    
    # Error with context and details
    full_error = BaseError(
        "Full error", 
        context="test_function",
        severity=ErrorSeverity.WARNING,
        details="Complete details"
    )
    print(f"Full error: {full_error}")
    
    print("✓ Error formatting test completed")


def test_handle_error_function():
    """Test handle_error function with visual feedback."""
    print("\n=== Testing handle_error Function ===")
    
    # Set up a logger that writes to stdout
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    # Test with different severity levels
    for severity in ErrorSeverity:
        print(f"\nTesting handle_error with {severity.name} severity:")
        error = BaseError("Test message", severity=severity)
        try:
            handle_error(error, logger)
            print(f"✓ Handled {severity.name} without exit")
        except SystemExit:
            print(f"✓ SystemExit raised for {severity.name} as expected")
    
    print("\n✓ handle_error function test completed")


def test_setup_logger_function():
    """Test setup_logger function with visual feedback."""
    print("\n=== Testing setup_logger Function ===")
    
    # Create a logger
    logger = setup_logger("test_logger", log_file="logs/test.log")
    
    # Log messages at different levels
    logger.debug("This is a DEBUG message")
    logger.info("This is an INFO message")
    logger.warning("This is a WARNING message")
    logger.error("This is an ERROR message")
    logger.critical("This is a CRITICAL message")
    
    print(f"Logger name: {logger.name}")
    print(f"Logger level: {logging.getLevelName(logger.level)}")
    print(f"Number of handlers: {len(logger.handlers)}")
    
    print("✓ setup_logger function test completed")


if __name__ == "__main__":
    # Run all tests with visual feedback
    print("\n=== Running Standalone Error Handling Tests ===\n")
    
    test_cases = [
        ("INFO severity", BaseError("Info test", severity=ErrorSeverity.INFO)),
        ("WARNING severity", BaseError("Warning test", severity=ErrorSeverity.WARNING)),
        ("ERROR severity without exit", BaseError("Error test", severity=ErrorSeverity.ERROR))
    ]
    
    # Set up a logger
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    # Run tests that don't exit
    for name, error in test_cases:
        print(f"\nTesting: {name}")
        handle_error(error, logger)
    
    # Run tests that exit (these will be skipped in normal execution)
    exit_test_cases = [
        ("CRITICAL severity", BaseError("Critical test", severity=ErrorSeverity.CRITICAL)),
        ("ERROR with exit_app=True", BaseError("Error test", severity=ErrorSeverity.ERROR), True),
    ]
    
    print("\nThe following tests would normally cause the program to exit:")
    for test in exit_test_cases:
        if len(test) == 2:
            name, error = test
            exit_app = False
        else:
            name, error, exit_app = test
        print(f"- {name}: {error} (exit_app={exit_app})")
    
    print("\n✓ All standalone tests completed successfully") 