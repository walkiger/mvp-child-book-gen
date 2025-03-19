"""
Tests for database utilities and error handling
"""
import os
import sqlite3
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock, call
from sqlalchemy import create_engine, text
import logging
from datetime import datetime, UTC

from management.db_utils import init_db, run_migrations, log_message
from app.core.errors.database import DatabaseError, with_db_error_handling
from app.core.errors.base import ErrorContext, ErrorSeverity, RetryConfig


@pytest.fixture
def error_context():
    """Create a test error context for database operations."""
    return ErrorContext(
        source="test.database",
        severity=ErrorSeverity.ERROR,
        timestamp=datetime.now(UTC),
        error_id="test-db-id",
        additional_data={"operation": "test"}
    )


@pytest.fixture(autouse=True)
def mock_error_handling():
    """Mock the error handling decorator for testing."""
    with patch('app.core.errors.database.with_db_error_handling') as mock:
        def wrapper(func=None):
            def inner(f):
                def wrapped(*args, **kwargs):
                    try:
                        return f(*args, **kwargs)
                    except Exception as e:
                        error_context = ErrorContext(
                            source="test.database",
                            severity=ErrorSeverity.ERROR,
                            timestamp=datetime.now(UTC),
                            additional_data={"function": f.__name__}
                        )
                        raise DatabaseError(str(e), error_context=error_context) from e
                return wrapped
            return inner(func) if func else inner
        mock.side_effect = wrapper
        yield mock


def test_init_db(temp_db_path):
    """Test database initialization using the temp_db_path fixture"""
    # Initialize the test database
    db_path = init_db(temp_db_path)
    assert db_path == temp_db_path
    
    # Verify that the database has the expected tables
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    
    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    expected_tables = [
        'migrations', 'users', 'stories', 'pages', 
        'characters', 'settings', 'images'
    ]
    
    for table in expected_tables:
        assert table in tables, f"Table {table} not found in database"
    
    conn.close()


def test_run_migrations_no_dir(temp_db_path, monkeypatch, temp_dir):
    """Test running migrations when no migrations directory exists"""
    # Initialize the test database
    init_db(temp_db_path)
    
    # Create a temporary directory structure without migrations
    temp_app_dir = os.path.join(temp_dir, "app")
    temp_db_dir = os.path.join(temp_app_dir, "database")
    os.makedirs(temp_db_dir, exist_ok=True)
    
    monkeypatch.setattr('os.getcwd', lambda: temp_dir)
    
    # Run migrations (should return False since no migrations directory exists)
    with pytest.raises(DatabaseError) as exc_info:
        run_migrations(temp_db_path)
    
    assert exc_info.value.error_code == "DB-MIG-001"
    assert "Migrations directory not found" in str(exc_info.value)
    assert exc_info.value.error_context.source == "database.migrations"
    assert exc_info.value.error_context.severity == ErrorSeverity.ERROR


def test_connection_error(temp_db_path):
    """Test handling of database connection errors"""
    # Create an invalid database path
    invalid_path = "/nonexistent/directory/db.sqlite3"
    
    # Attempt to initialize database at invalid path
    with pytest.raises(DatabaseError) as exc_info:
        init_db(invalid_path)
    
    assert exc_info.value.error_code == "DB-CONN-001"
    assert "Could not connect to database" in str(exc_info.value)
    assert exc_info.value.error_context.source == "database.connection"
    assert exc_info.value.error_context.severity == ErrorSeverity.ERROR
    assert "path" in exc_info.value.error_context.additional_data


def test_file_permission_error(temp_db_path, temp_dir):
    """Test handling of file permission errors"""
    # Create a read-only directory
    readonly_dir = os.path.join(temp_dir, "readonly")
    os.makedirs(readonly_dir, exist_ok=True)
    os.chmod(readonly_dir, 0o444)  # Read-only permissions
    
    db_path = os.path.join(readonly_dir, "db.sqlite3")
    
    # Attempt to initialize database in read-only directory
    with pytest.raises(DatabaseError) as exc_info:
        init_db(db_path)
    
    assert exc_info.value.error_code == "DB-PERM-001"
    assert "Permission denied" in str(exc_info.value)
    assert exc_info.value.error_context.source == "database.permissions"
    assert exc_info.value.error_context.severity == ErrorSeverity.ERROR
    assert "path" in exc_info.value.error_context.additional_data
    
    # Cleanup: restore permissions to allow directory deletion
    os.chmod(readonly_dir, 0o755)


def test_corrupt_database(temp_db_path):
    """Test handling of corrupt database"""
    # Create a corrupt database file
    with open(temp_db_path, 'w') as f:
        f.write("corrupt data")
    
    # Attempt to use corrupt database
    with pytest.raises(DatabaseError) as exc_info:
        init_db(temp_db_path)
    
    assert exc_info.value.error_code == "DB-CORRUPT-001"
    assert "Database is corrupted" in str(exc_info.value)
    assert exc_info.value.error_context.source == "database.integrity"
    assert exc_info.value.error_context.severity == ErrorSeverity.ERROR
    assert "path" in exc_info.value.error_context.additional_data


def test_migration_error(temp_db_path, temp_dir):
    """Test handling of migration errors"""
    # Initialize the test database
    init_db(temp_db_path)
    
    # Create a temporary migrations directory with a failing migration
    migrations_dir = os.path.join(temp_dir, "app", "database", "migrations")
    os.makedirs(migrations_dir, exist_ok=True)
    
    # Create a failing migration file
    migration_content = '''
def migrate(engine):
    """Test migration that fails"""
    raise Exception("Migration failed")
'''
    with open(os.path.join(migrations_dir, "001_failing_migration.py"), "w") as f:
        f.write(migration_content)
    
    # Run migrations
    with patch('os.getcwd', return_value=temp_dir):
        with pytest.raises(DatabaseError) as exc_info:
            run_migrations(temp_db_path)
    
    assert exc_info.value.error_code == "DB-MIG-002"
    assert "Migration failed" in str(exc_info.value)
    assert exc_info.value.error_context.source == "database.migrations"
    assert exc_info.value.error_context.severity == ErrorSeverity.ERROR
    assert "migration" in exc_info.value.error_context.additional_data


@pytest.mark.parametrize("error_type,expected_code,expected_message", [
    (sqlite3.OperationalError("database is locked"), "DB-LOCK-001", "Database is locked"),
    (sqlite3.IntegrityError("UNIQUE constraint failed"), "DB-INTEG-001", "Integrity error"),
    (sqlite3.DatabaseError("generic error"), "DB-GEN-001", "Database error"),
    (Exception("unexpected error"), "DB-UNEXPECTED-001", "Unexpected error"),
])
def test_error_handler_types(temp_db_path, error_type, expected_code, expected_message):
    """Test different types of database errors"""
    
    @with_db_error_handling
    def failing_operation():
        raise error_type
    
    with pytest.raises(DatabaseError) as exc_info:
        failing_operation()
    
    assert exc_info.value.error_code == expected_code
    assert expected_message in str(exc_info.value)
    assert exc_info.value.error_context.source.startswith("database")
    assert exc_info.value.error_context.severity == ErrorSeverity.ERROR


def test_database_logging(temp_db_path, caplog):
    """Test database operation logging"""
    caplog.set_level(logging.INFO)
    
    # Test successful operation logging
    init_db(temp_db_path)
    
    assert any(
        record.levelname == "INFO" and
        "Initialized database" in record.message
        for record in caplog.records
    )
    
    # Test error logging
    with pytest.raises(DatabaseError):
        init_db("/invalid/path")
    
    assert any(
        record.levelname == "ERROR" and
        "Failed to initialize database" in record.message and
        "error_code" in record.message
        for record in caplog.records
    )


def test_retry_mechanism(temp_db_path):
    """Test database operation retry mechanism"""
    attempts = []
    
    @with_db_error_handling
    def failing_operation():
        attempts.append(1)
        if len(attempts) < 3:
            raise sqlite3.OperationalError("database is locked")
        return "success"
    
    # Configure retry
    retry_config = RetryConfig(
        max_retries=3,
        delay_seconds=0.1,
        exponential_backoff=True
    )
    
    result = failing_operation()
    assert result == "success"
    assert len(attempts) == 3


def test_error_context_data(temp_db_path, error_context):
    """Test error context data in database operations"""
    
    @with_db_error_handling
    def operation_with_context():
        raise DatabaseError(
            "Operation failed",
            error_code="DB-TEST-001",
            error_context=error_context
        )
    
    with pytest.raises(DatabaseError) as exc_info:
        operation_with_context()
    
    assert exc_info.value.error_code == "DB-TEST-001"
    assert exc_info.value.error_context == error_context
    assert exc_info.value.error_context.source == "test.database"
    assert exc_info.value.error_context.additional_data["operation"] == "test"


def test_log_message_function(temp_db_path):
    """Test the log_message function with error context"""
    # Test successful message logging
    log_message(
        "Test message",
        level=logging.INFO,
        error_context=ErrorContext(
            source="test.logging",
            severity=ErrorSeverity.INFO,
            additional_data={"test": "data"}
        )
    )
    
    # Test error message logging
    with pytest.raises(DatabaseError) as exc_info:
        log_message(
            "Error message",
            level=logging.ERROR,
            error_context=ErrorContext(
                source="test.logging",
                severity=ErrorSeverity.ERROR,
                additional_data={"error": "test"}
            ),
            raise_error=True
        )
    
    assert exc_info.value.error_code == "DB-LOG-001"
    assert exc_info.value.error_context.source == "test.logging"
    assert exc_info.value.error_context.severity == ErrorSeverity.ERROR 