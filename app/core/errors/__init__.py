"""
Error handling package initialization.

This module exposes all error classes for the application.
"""

# Import base errors first
from .base import (
    BaseError,
    ErrorContext,
    ErrorSeverity,
    ConfigurationError,
)

# Import API errors
from .api import (
    APIError,
    RequestError,
    ResponseError,
    NotFoundError,
    InternalServerError,
    ValidationError,
    ExternalAPIError,
)

# Import database errors
from .database import (
    DatabaseError,
    DatabaseConnectionError,
    DatabaseInitializationError,
    DatabaseSeedingError,
    QueryError,
    TransactionError,
    IntegrityError,
    MigrationError as DatabaseMigrationError,
)

# Import auth errors
from .auth import (
    AuthError,
    AuthenticationError,
    AuthorizationError,
    TokenError,
    SessionError,
    RegistrationError,
    AuthValidationError,
)

# Import user errors
from .user import (
    UserError,
    UserValidationError,
)

__all__ = [
    # Base errors
    'BaseError',
    'ErrorContext',
    'ErrorSeverity',
    'ConfigurationError',
    
    # API errors
    'APIError',
    'RequestError',
    'ResponseError',
    'NotFoundError',
    'InternalServerError',
    'ValidationError',
    'ExternalAPIError',
    
    # Database errors
    'DatabaseError',
    'DatabaseConnectionError',
    'DatabaseInitializationError',
    'DatabaseSeedingError',
    'QueryError',
    'TransactionError',
    'IntegrityError',
    'DatabaseMigrationError',
    
    # Auth errors
    'AuthError',
    'AuthenticationError',
    'AuthorizationError',
    'TokenError',
    'SessionError',
    'RegistrationError',
    'AuthValidationError',
    
    # User errors
    'UserError',
    'UserValidationError',
] 