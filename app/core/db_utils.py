"""
Database utilities for managing database operations and migrations.
"""

import sqlite3
import os
import importlib.util
from datetime import datetime, UTC
from uuid import uuid4
import logging

from app.core.errors.database import (
    DatabaseError,
    ConnectionError,
    MigrationError,
    TransactionError
)
from app.core.errors.base import ErrorContext

logger = logging.getLogger(__name__)

def run_migrations(db_path: str, migrations_dir: str) -> None:
    """
    Run database migrations.

    Args:
        db_path: Path to the SQLite database file
        migrations_dir: Directory containing migration files

    Raises:
        ConnectionError: If database connection fails
        MigrationError: If migration execution fails
        TransactionError: If transaction management fails
    """
    conn = None
    try:
        # Connect to database
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
        except sqlite3.Error as e:
            raise ConnectionError(
                message=f"Failed to connect to database: {db_path}",
                error_code="DB-CONN-FAIL-001",
                context=ErrorContext(
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={"error": str(e)}
                )
            )

        # Create migrations table if it doesn't exist
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS migrations (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        except sqlite3.Error as e:
            raise MigrationError(
                message="Failed to create migrations table",
                error_code="DB-MIG-INIT-001",
                context=ErrorContext(
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={"error": str(e)}
                )
            )

        # Get list of applied migrations
        try:
            cursor.execute("SELECT name FROM migrations")
            applied_migrations = {row[0] for row in cursor.fetchall()}
        except sqlite3.Error as e:
            raise MigrationError(
                message="Failed to fetch applied migrations",
                error_code="DB-MIG-FETCH-001",
                context=ErrorContext(
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={"error": str(e)}
                )
            )

        # Get list of migration files
        try:
            migration_files = sorted([
                f for f in os.listdir(migrations_dir)
                if f.endswith('.py') and not f.startswith('__')
            ])
        except OSError as e:
            raise MigrationError(
                message=f"Failed to read migrations directory: {migrations_dir}",
                error_code="DB-MIG-READ-001",
                context=ErrorContext(
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={"error": str(e)}
                )
            )

        # Apply each migration
        for migration_file in migration_files:
            if migration_file not in applied_migrations:
                try:
                    logger.info(f"Applying migration: {migration_file}")
                except Exception as e:
                    logger.error(f"Failed to log migration start: {str(e)}")
                    
                # Load and execute migration
                try:
                    spec = importlib.util.spec_from_file_location(
                        migration_file,
                        os.path.join(migrations_dir, migration_file)
                    )
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                except Exception as e:
                    raise MigrationError(
                        message=f"Failed to load migration file: {migration_file}",
                        error_code="DB-MIG-LOAD-001",
                        context=ErrorContext(
                            timestamp=datetime.now(UTC),
                            error_id=str(uuid4()),
                            additional_data={
                                "file": migration_file,
                                "error": str(e)
                            }
                        )
                    )
                
                # Start transaction
                try:
                    conn.execute("BEGIN TRANSACTION")
                    
                    # Run migration
                    module.up(conn)
                    
                    # Record migration
                    cursor.execute(
                        "INSERT INTO migrations (name) VALUES (?)",
                        (migration_file,)
                    )
                    conn.commit()
                    
                    logger.info(f"Successfully applied migration: {migration_file}")
                except sqlite3.Error as e:
                    conn.rollback()
                    raise TransactionError(
                        message=f"Transaction failed for migration: {migration_file}",
                        error_code="DB-TRANS-FAIL-001",
                        context=ErrorContext(
                            timestamp=datetime.now(UTC),
                            error_id=str(uuid4()),
                            additional_data={
                                "file": migration_file,
                                "error": str(e)
                            }
                        )
                    )
                except Exception as e:
                    conn.rollback()
                    raise MigrationError(
                        message=f"Migration failed: {migration_file}",
                        error_code="DB-MIG-EXEC-001",
                        context=ErrorContext(
                            timestamp=datetime.now(UTC),
                            error_id=str(uuid4()),
                            additional_data={
                                "file": migration_file,
                                "error": str(e)
                            }
                        )
                    )

    except DatabaseError:
        # Re-raise database errors as they're already properly formatted
        raise
    except Exception as e:
        # Catch any unexpected errors and wrap them
        raise DatabaseError(
            message="Unexpected database error",
            error_code="DB-UNEXPECTED-001",
            context=ErrorContext(
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"error": str(e)}
            )
        )
    finally:
        if conn:
            conn.close() 