"""
Database utilities for managing the application database
"""

import os
import sys
import sqlite3
import importlib.util
from pathlib import Path
import datetime

from .errors import DatabaseError, ErrorSeverity, handle_error, setup_logger, db_error_handler, with_error_handling

# Setup logger
logger = setup_logger()

# Default database path
DEFAULT_DB_PATH = os.path.join(os.getcwd(), "storybook.db")
# Log file path
LOG_FILE_PATH = os.path.join(os.getcwd(), "logs", "db_operations.log")

def log_message(message):
    """Write a message to the log file and print it to console."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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

@db_error_handler
@with_error_handling(context="Database Initialization")
def init_db(db_path=None):
    """Initialize the database with the basic schema.
    
    Args:
        db_path: Optional custom path for the database file
    """
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    
    log_message("\n=== DATABASE INITIALIZATION ===")
    log_message(f"Database path: {db_path}")
    
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

@db_error_handler
@with_error_handling(context="Database Migrations")
def run_migrations(db_path=None):
    """Run all migration scripts in the migrations directory.
    
    Args:
        db_path: Optional custom path for the database file
    """
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    
    log_message("\n=== RUNNING DATABASE MIGRATIONS ===")
    
    # Ensure app path is in sys.path
    app_path = os.getcwd()
    if app_path not in sys.path:
        sys.path.append(app_path)
    
    # Look for migrations in the app directory
    migrations_dir = os.path.join(app_path, "app", "database", "migrations")
    if not os.path.exists(migrations_dir):
        log_message(f"Migration directory not found: {migrations_dir}")
        log_message("=== MIGRATION FAILED ===\n")
        return False
        
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
    
    log_message(f"Found {len(migration_files)} migration files.")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create migrations table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS migrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Get already applied migrations
    cursor.execute("SELECT name FROM migrations")
    applied_migrations = [row[0] for row in cursor.fetchall()]
    
    # Run migrations that haven't been applied yet
    successful_migrations = 0
    
    for file_path in sorted(migration_files):
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
                module.migrate()
                
                # Mark as applied
                cursor.execute("INSERT INTO migrations (name) VALUES (?)", (migration_name,))
                conn.commit()
                
                successful_migrations += 1
                log_message(f"Successfully applied migration: {migration_name}")
            else:
                log_message(f"Error: Migration {migration_name} does not have a migrate() function.")
        except Exception as e:
            log_message(f"Error applying migration {migration_name}: {str(e)}")
            conn.rollback()
            log_message("=== MIGRATION FAILED ===\n")
            raise DatabaseError(f"Migration failed: {migration_name}", details=str(e))
    
    conn.close()
    
    if successful_migrations > 0:
        log_message(f"Successfully applied {successful_migrations} migrations.")
    else:
        log_message("No new migrations to apply.")
    
    log_message("=== MIGRATION COMPLETE ===\n")
    
    return True 