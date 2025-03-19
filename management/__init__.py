"""
Management package for the Child Book Generator MVP.

This package provides utilities for managing the application, including:
- Server management (start, stop, status)
- Database management (initialization, migrations)
- Environment setup and configuration
- Process management
- Content and database inspection
- Error handling utilities
- Monitoring and health checks
"""

import logging
from app.core.logging import setup_logger

# Setup logger
logger = setup_logger(
    name="management",
    level="INFO",
    log_file="logs/management.log"
)

from .server_utils import show_status, DEFAULT_BACKEND_PORT, DEFAULT_FRONTEND_PORT
from .commands import (
    start_backend, start_frontend, stop_server,
    run_db_init, run_migrations
)
from .db_inspection import check_db_structure, explore_db_contents, dump_db_to_file
from .content_inspection import check_characters, check_images
from .env_commands import setup_environment, show_current_env

# Import monitoring utilities
try:
    from .monitoring import (
        generate_monitoring_report, print_monitoring_summary, save_monitoring_report,
        monitor_backend, monitor_frontend, check_system_resources
    )
except ImportError:
    # If monitoring modules are not available, provide placeholders
    pass

# Import error handling utilities
from app.core.errors.base import (
    BaseError, ErrorSeverity, ErrorContext
)
from app.core.errors.management import (
    ServerError,
    ProcessError,
    ManagementDatabaseError as DatabaseError,
    CommandError,
    EnvironmentError,
    MonitoringError,
    with_management_error_handling as with_error_handling
)

__version__ = "1.0.0"

# Define exports
__all__ = [
    # Server utilities
    'show_status',
    'DEFAULT_BACKEND_PORT',
    'DEFAULT_FRONTEND_PORT',
    'start_backend',
    'start_frontend',
    'stop_server',
    
    # Database utilities
    'run_db_init', 
    'run_migrations',
    'check_db_structure',
    'explore_db_contents',
    'dump_db_to_file',
    
    # Content inspection utilities
    'check_characters',
    'check_images',
    
    # Environment management utilities
    'setup_environment',
    'show_current_env',
    
    # Error handling
    'BaseError',
    'ServerError',
    'ProcessError',
    'DatabaseError',
    'CommandError',
    'EnvironmentError',
    'MonitoringError',
    'ErrorSeverity',
    'ErrorContext',
    'setup_logger',
    'with_error_handling'
] 