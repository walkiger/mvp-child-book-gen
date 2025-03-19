"""
Logging utilities for the application.

This module provides logging setup and configuration utilities.
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional, Union

from .errors.base import ErrorContext, ErrorSeverity, ConfigurationError

# Global logger instance
_root_logger = None

def setup_logger(
    name: str,
    log_file: str,
    level: Union[str, int] = "INFO",
    max_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Set up a logger with file and console handlers.

    Args:
        name: Logger name
        log_file: Path to log file
        level: Logging level (default: INFO) - can be string or integer
        max_size: Maximum size of log file before rotation in bytes (default: 10MB)
        backup_count: Number of backup files to keep (default: 5)

    Returns:
        logging.Logger: Configured logger instance

    Raises:
        ConfigurationError: If logger setup fails
    """
    try:
        global _root_logger
        
        # Convert level to integer if it's a string
        if isinstance(level, str):
            level = getattr(logging, level.upper())
        
        # If root logger exists, return a child logger
        if _root_logger is not None:
            child_logger = logging.getLogger(name)
            child_logger.handlers = []  # Remove any existing handlers
            child_logger.setLevel(level)
            child_logger.parent = _root_logger
            return child_logger
        
        # Create root logger
        _root_logger = logging.getLogger()
        _root_logger.handlers = []  # Remove any existing handlers
        _root_logger.setLevel(level)

        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(levelname)s - %(message)s'
        )

        # File handler with rotation
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_size,
            backupCount=backup_count
        )
        file_handler.setFormatter(file_formatter)
        _root_logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        _root_logger.addHandler(console_handler)

        # Create and return a child logger
        child_logger = logging.getLogger(name)
        child_logger.setLevel(level)
        return child_logger

    except Exception as e:
        error_context = ErrorContext(
            source="logging.setup_logger",
            severity=ErrorSeverity.ERROR,
            timestamp=datetime.now(),
            additional_data={
                "logger_name": name,
                "log_file": log_file,
                "error": str(e)
            }
        )
        raise ConfigurationError(
            message=f"Failed to setup logger: {str(e)}",
            error_code="LOG-SETUP-001",
            context=error_context
        )

# Default application logger
app_logger = setup_logger(
    name="app",
    level="INFO",
    log_file="logs/app.log"
) 