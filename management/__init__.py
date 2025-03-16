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

from .main import main
from .server_utils import show_status, DEFAULT_BACKEND_PORT, DEFAULT_FRONTEND_PORT
from .commands import (
    start_backend, start_frontend, stop_server,
    run_db_init, run_migrations
)
from .db_inspection import check_db_structure, explore_db_contents, dump_db_to_file
from .content_inspection import check_characters, check_images
from .env_commands import setup_environment, show_current_env
try:
    from .monitoring import (
        generate_monitoring_report, print_monitoring_summary, save_monitoring_report,
        monitor_backend, monitor_frontend, check_system_resources
    )
except ImportError:
    # If monitoring modules are not available, provide placeholders
    pass
from .errors import ProcessError

__version__ = "1.0.0"

# Import from shared utils
from utils.error_handling import (
    BaseError, ServerError, DatabaseError, ConfigError, ResourceError,
    InputError, ImageError, ErrorSeverity, handle_error, setup_logger,
    with_retry, ManagedResource, CircuitBreaker
)

# Import these conditionally to avoid errors if files don't exist yet
try:
    from .db_inspection import check_db_structure, explore_db_contents, dump_db_to_file
    from .content_inspection import check_characters, check_images
    __all__ = [
        # Main entry point
        'main', 
        
        # Database utilities
        'init_db', 
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
        'setup_project',
        'integrate_migrations',
        
        # Error handling
        'BaseError',
        'ServerError',
        'ProcessError',
        'DatabaseError',
        'ConfigError',
        'ResourceError',
        'InputError',
        'ImageError',
        'ErrorSeverity',
        'handle_error',
        'setup_logger',
        'with_error_handling',
        'db_error_handler',
        'with_retry',
        'ManagedResource',
        'CircuitBreaker',
    ]
except ImportError:
    # Limited exports if inspection modules aren't available
    __all__ = [
        'main',
        'init_db',
        'run_migrations',
        'setup_environment',
        'show_current_env',
        'setup_project',
        'integrate_migrations',
        'BaseError',
        'ServerError',
        'ProcessError',
        'DatabaseError',
        'ConfigError',
        'ResourceError',
        'InputError',
        'ImageError',
        'ErrorSeverity',
        'handle_error',
        'setup_logger',
        'with_error_handling',
        'db_error_handler',
        'with_retry',
        'ManagedResource',
        'CircuitBreaker',
    ] 