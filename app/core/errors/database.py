"""
Database Error Handling

This module defines database-specific errors extending the base error system.
"""

from typing import Optional, Dict, Any, List

from .base import BaseError, ErrorContext, ErrorSeverity


class DatabaseError(BaseError):
    """Base class for all database-related errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        http_status_code: int = 500,
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None
    ):
        if not error_code.startswith('DATABASE-'):
            error_code = f"DATABASE-{error_code}"
        super().__init__(
            message,
            error_code,
            http_status_code,
            context,
            details,
            suggestions
        )


class DatabaseConnectionError(DatabaseError):
    """Database connection failures."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "DATABASE-CONNECTION-FAILURE-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message,
            error_code,
            http_status_code=503,
            context=context,
            details=details,
            suggestions=[
                "Check database connection settings",
                "Verify database server is running",
                "Check network connectivity"
            ]
        )
        self.set_severity(ErrorSeverity.CRITICAL)


class DatabaseInitializationError(DatabaseError):
    """Database initialization failures."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "DATABASE-INIT-FAILURE-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message,
            error_code,
            http_status_code=500,
            context=context,
            details=details,
            suggestions=[
                "Check database schema and migrations",
                "Verify database user permissions",
                "Check initialization scripts for errors"
            ]
        )
        self.set_severity(ErrorSeverity.CRITICAL)


class DatabaseSeedingError(DatabaseError):
    """Database seeding failures."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "DATABASE-SEED-FAILURE-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message,
            error_code,
            http_status_code=500,
            context=context,
            details=details,
            suggestions=[
                "Check seed data format and content",
                "Verify database constraints",
                "Ensure all required relationships exist",
                "Check for duplicate entries"
            ]
        )


class QueryError(DatabaseError):
    """Query execution failures."""
    
    def __init__(
        self,
        message: str,
        query: str,
        error_code: str = "DATABASE-QUERY-FAILURE-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            'query': query
        })
        
        super().__init__(
            message,
            error_code,
            http_status_code=500,
            context=context,
            details=details,
            suggestions=[
                "Check query syntax",
                "Verify table and column names",
                "Check data types match"
            ]
        )
        self.set_severity(ErrorSeverity.ERROR)


class TransactionError(DatabaseError):
    """Transaction management failures."""
    
    def __init__(
        self,
        message: str,
        transaction_id: str,
        error_code: str = "DATABASE-TRANSACTION-FAILURE-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            'transaction_id': transaction_id
        })
        
        super().__init__(
            message,
            error_code,
            http_status_code=500,
            context=context,
            details=details,
            suggestions=[
                "Check transaction isolation level",
                "Verify transaction boundaries",
                "Check for deadlocks"
            ]
        )
        self.set_severity(ErrorSeverity.ERROR)


class IntegrityError(DatabaseError):
    """Data integrity constraint violations."""
    
    def __init__(
        self,
        message: str,
        constraint_name: str,
        error_code: str = "DATABASE-INTEGRITY-FAILURE-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            'constraint_name': constraint_name
        })
        
        super().__init__(
            message,
            error_code,
            http_status_code=400,
            context=context,
            details=details,
            suggestions=[
                "Check constraint definitions",
                "Verify data meets constraints",
                "Review foreign key relationships"
            ]
        )
        self.set_severity(ErrorSeverity.ERROR)


class MigrationError(DatabaseError):
    """Database migration failures."""
    
    def __init__(
        self,
        message: str,
        migration_name: str,
        error_code: str = "DATABASE-MIGRATION-FAILURE-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            'migration_name': migration_name
        })
        
        super().__init__(
            message,
            error_code,
            http_status_code=500,
            context=context,
            details=details,
            suggestions=[
                "Check migration sequence",
                "Verify schema changes",
                "Review data transformations"
            ]
        )
        self.set_severity(ErrorSeverity.ERROR) 