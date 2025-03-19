"""
Database utilities for managing the application database
"""

import os
import sys
import sqlite3
import importlib.util
from pathlib import Path
import logging
from datetime import datetime, UTC
from uuid import uuid4
from sqlalchemy import create_engine, text

from app.core.errors.management import (
    ManagementDatabaseError,
    with_management_error_handling
)
from app.core.errors.base import ErrorContext, ErrorSeverity
from app.core.logging import setup_logger

# Setup logger
logger = setup_logger(
    name="management.db_utils",
    level="INFO",
    log_file="logs/management.log"
)

# Default database path
DEFAULT_DB_PATH = os.path.join(os.getcwd(), "storybook.db")
# Log file path
LOG_FILE_PATH = os.path.join(os.getcwd(), "logs", "db_operations.log")

def log_message(message):
    """Write a message to the log file and print it to console."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    
    # Ensure logs directory exists
    os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
    
    # Write to log file
    try:
        with open(LOG_FILE_PATH, "a") as log_file:
            log_file.write(log_entry + "\n")
    except OSError as e:
        logger.warning(f"Could not write to log file: {str(e)}")
    
    # Log to console using our logger
    logger.info(message)

@with_management_error_handling
def init_db(db_path=None):
    """Initialize the database with the basic schema.
    
    Args:
        db_path: Optional custom path for the database file
    """
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    
    log_message("\n=== DATABASE INITIALIZATION ===")
    log_message(f"Database path: {db_path}")
    
    try:
        # Connect to the database (will create it if it doesn't exist)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        log_message("Connected to database")
        
        # Create the migrations table to track applied migrations
        log_message("Creating migrations table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create the users table
        log_message("Creating users table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create stories table
        log_message("Creating stories table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS stories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            age_range TEXT,
            theme TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # Create pages table
        log_message("Creating pages table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER NOT NULL,
            page_number INTEGER NOT NULL,
            content TEXT NOT NULL,
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (story_id) REFERENCES stories (id),
            UNIQUE(story_id, page_number)
        )
        ''')
        
        # Create characters table
        log_message("Creating characters table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS characters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (story_id) REFERENCES stories (id)
        )
        ''')
        
        # Create settings table
        log_message("Creating settings table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL UNIQUE,
            value TEXT,
            description TEXT
        )
        ''')

        # Create images table
        log_message("Creating images table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            path TEXT NOT NULL,
            type TEXT NOT NULL,
            width INTEGER,
            height INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # Commit the changes and close the connection
        conn.commit()
        conn.close()
        
        log_message("Database initialized successfully")
        log_message("=== INITIALIZATION COMPLETE ===\n")
        
        return db_path
        
    except sqlite3.Error as e:
        raise ManagementDatabaseError(
            message="Failed to initialize database",
            context=ErrorContext(
                source="management.db_utils.init_db",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={
                    "db_path": db_path,
                    "error": str(e)
                }
            )
        )

@with_management_error_handling
def run_migrations(db_path=None):
    """Run all migration scripts in the migrations directory.
    
    Args:
        db_path: Optional custom path for the database file
    """
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    
    log_message("\n=== RUNNING DATABASE MIGRATIONS ===")
    
    try:
        # Ensure app path is in sys.path
        app_path = os.getcwd()
        if app_path not in sys.path:
            sys.path.append(app_path)
        
        # Look for migrations in the app directory
        migrations_dir = os.path.join(app_path, "app", "database", "migrations")
        if not os.path.exists(migrations_dir):
            raise ManagementDatabaseError(
                message="Migration directory not found",
                context=ErrorContext(
                    source="management.db_utils.run_migrations",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "migrations_dir": migrations_dir
                    }
                )
            )
        
        migration_files = []
        
        # Look for Python files in the migrations directory
        for file_path in Path(migrations_dir).glob("*.py"):
            if file_path.name.startswith("__"):
                continue
            migration_files.append(file_path)
        
        if not migration_files:
            log_message("No migration files found.")
            log_message("=== MIGRATION COMPLETE (NO FILES) ===\n")
            return False
        
        # Sort migration files by name to ensure consistent order
        migration_files.sort(key=lambda x: x.name)
        
        log_message(f"Found {len(migration_files)} migration files.")
        
        try:
            # Create SQLAlchemy engine
            engine = create_engine(f"sqlite:///{db_path}")
            
            # Create migrations table if it doesn't exist
            with engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS migrations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                conn.commit()
            
            # Get already applied migrations
            with engine.connect() as conn:
                result = conn.execute(text("SELECT name FROM migrations"))
                applied_migrations = [row[0] for row in result]
            
            # Run migrations that haven't been applied yet
            successful_migrations = 0
            
            for file_path in migration_files:
                migration_name = file_path.stem
                
                if migration_name in applied_migrations:
                    log_message(f"Migration {migration_name} already applied, skipping.")
                    continue
                
                log_message(f"Applying migration: {migration_name}")
                
                try:
                    # Load the migration module
                    spec = importlib.util.spec_from_file_location(migration_name, file_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Run the migration
                    if hasattr(module, "migrate"):
                        module.migrate(engine)  # Pass the engine to the migrate function
                        
                        # Mark as applied
                        with engine.connect() as conn:
                            conn.execute(
                                text("INSERT INTO migrations (name) VALUES (:name)"),
                                {"name": migration_name}
                            )
                            conn.commit()
                        
                        successful_migrations += 1
                        log_message(f"Successfully applied migration: {migration_name}")
                    else:
                        raise ManagementDatabaseError(
                            message=f"Migration {migration_name} has no migrate function",
                            context=ErrorContext(
                                source="management.db_utils.run_migrations",
                                severity=ErrorSeverity.ERROR,
                                timestamp=datetime.now(UTC),
                                error_id=str(uuid4()),
                                additional_data={
                                    "migration_name": migration_name,
                                    "file_path": str(file_path)
                                }
                            )
                        )
                        
                except Exception as e:
                    raise ManagementDatabaseError(
                        message=f"Failed to apply migration {migration_name}",
                        context=ErrorContext(
                            source="management.db_utils.run_migrations",
                            severity=ErrorSeverity.ERROR,
                            timestamp=datetime.now(UTC),
                            error_id=str(uuid4()),
                            additional_data={
                                "migration_name": migration_name,
                                "file_path": str(file_path),
                                "error": str(e)
                            }
                        )
                    )
            
            log_message(f"Successfully applied {successful_migrations} migrations")
            log_message("=== MIGRATION COMPLETE ===\n")
            return True
            
        except Exception as e:
            raise ManagementDatabaseError(
                message="Failed to run migrations",
                context=ErrorContext(
                    source="management.db_utils.run_migrations",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "db_path": db_path,
                        "error": str(e)
                    }
                )
            )
            
    except Exception as e:
        raise ManagementDatabaseError(
            message="Failed to run migrations",
            context=ErrorContext(
                source="management.db_utils.run_migrations",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={
                    "db_path": db_path,
                    "error": str(e)
                }
            )
        ) 