"""
Database migration utilities.
"""
import os
import sys
from datetime import datetime, UTC
from uuid import uuid4
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.database.models import Base
from app.core.errors.base import ErrorContext, ErrorSeverity
from app.core.errors.database import DatabaseMigrationError

def create_migration_script():
    """Create a new migration script with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    migration_name = f"migration_{timestamp}.py"
    migration_path = os.path.join(os.path.dirname(__file__), "migrations", migration_name)
    
    try:
        os.makedirs(os.path.dirname(migration_path), exist_ok=True)
    except OSError as e:
        error_context = ErrorContext(
            source="migrations.create_migration_script",
            severity=ErrorSeverity.ERROR,
            timestamp=datetime.now(UTC),
            error_id=str(uuid4()),
            additional_data={"migration_path": migration_path, "error": str(e)}
        )
        raise DatabaseMigrationError(
            message=f"Failed to create migrations directory: {str(e)}",
            error_code="DB-MIG-DIR-001",
            context=error_context
        )
    
    template = f'''"""
Migration script created at {timestamp}
"""
from sqlalchemy import text
from app.database.models import Base

def upgrade(engine):
    """Upgrade database schema."""
    with engine.connect() as conn:
        # Create temporary table for images
        conn.execute(text("""
            CREATE TABLE images_new (
                id INTEGER PRIMARY KEY,
                story_id INTEGER,
                character_id INTEGER,
                image_data BLOB NOT NULL,
                image_format VARCHAR NOT NULL,
                generation_cost FLOAT,
                dalle_version VARCHAR NOT NULL,
                generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (story_id) REFERENCES stories(id),
                FOREIGN KEY (character_id) REFERENCES characters(id)
            )
        """))
        
        # Copy data from old table to new table
        conn.execute(text("""
            INSERT INTO images_new (id, story_id, character_id, image_data, image_format, generation_cost, dalle_version, generated_at)
            SELECT id, story_id, character_id, 
                   CAST(image_path AS BLOB), 
                   'png',  -- Default format
                   generation_cost,
                   'dall-e-3',  -- Default version
                   generated_at
            FROM images
        """))
        
        # Drop old table
        conn.execute(text("DROP TABLE images"))
        
        # Rename new table to original name
        conn.execute(text("ALTER TABLE images_new RENAME TO images"))
        
        # Update Character table
        conn.execute(text("""
            ALTER TABLE characters 
            ADD COLUMN dalle_version VARCHAR DEFAULT 'dall-e-3'
        """))
        
        conn.commit()

def downgrade(engine):
    """Downgrade database schema."""
    with engine.connect() as conn:
        # Create temporary table for images
        conn.execute(text("""
            CREATE TABLE images_old (
                id INTEGER PRIMARY KEY,
                story_id INTEGER,
                character_id INTEGER,
                image_path VARCHAR NOT NULL,
                generation_cost FLOAT,
                generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (story_id) REFERENCES stories(id),
                FOREIGN KEY (character_id) REFERENCES characters(id)
            )
        """))
        
        # Copy data from new table to old table
        conn.execute(text("""
            INSERT INTO images_old (id, story_id, character_id, image_path, generation_cost, generated_at)
            SELECT id, story_id, character_id, 
                   CAST(image_data AS VARCHAR),  -- Convert BLOB to string
                   generation_cost,
                   generated_at
            FROM images
        """))
        
        # Drop new table
        conn.execute(text("DROP TABLE images"))
        
        # Rename old table to original name
        conn.execute(text("ALTER TABLE images_old RENAME TO images"))
        
        # Remove dalle_version from Character table
        conn.execute(text("""
            ALTER TABLE characters 
            DROP COLUMN dalle_version
        """))
        
        conn.commit()
'''
    
    try:
        with open(migration_path, "w") as f:
            f.write(template)
    except IOError as e:
        error_context = ErrorContext(
            source="migrations.create_migration_script",
            severity=ErrorSeverity.ERROR,
            timestamp=datetime.now(UTC),
            error_id=str(uuid4()),
            additional_data={"migration_path": migration_path, "error": str(e)}
        )
        raise DatabaseMigrationError(
            message=f"Failed to write migration script: {str(e)}",
            error_code="DB-MIG-WRITE-001",
            context=error_context
        )
    
    print(f"Created migration script: {migration_path}")
    return migration_path

def run_migrations():
    """Run all pending migrations."""
    try:
        engine = create_engine(settings.DATABASE_URL)
    except SQLAlchemyError as e:
        error_context = ErrorContext(
            source="migrations.run_migrations",
            severity=ErrorSeverity.CRITICAL,
            timestamp=datetime.now(UTC),
            error_id=str(uuid4()),
            additional_data={"database_url": settings.DATABASE_URL, "error": str(e)}
        )
        raise DatabaseMigrationError(
            message=f"Failed to create database engine: {str(e)}",
            error_code="DB-MIG-ENGINE-001",
            context=error_context
        )
    
    # Create migrations table if it doesn't exist
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS migrations (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
    except SQLAlchemyError as e:
        error_context = ErrorContext(
            source="migrations.run_migrations",
            severity=ErrorSeverity.CRITICAL,
            timestamp=datetime.now(UTC),
            error_id=str(uuid4()),
            additional_data={"error": str(e)}
        )
        raise DatabaseMigrationError(
            message=f"Failed to create migrations table: {str(e)}",
            error_code="DB-MIG-TABLE-001",
            context=error_context
        )
    
    # Get list of applied migrations
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM migrations"))
            applied_migrations = {row[0] for row in result}
    except SQLAlchemyError as e:
        error_context = ErrorContext(
            source="migrations.run_migrations",
            severity=ErrorSeverity.ERROR,
            timestamp=datetime.now(UTC),
            error_id=str(uuid4()),
            additional_data={"error": str(e)}
        )
        raise DatabaseMigrationError(
            message=f"Failed to fetch applied migrations: {str(e)}",
            error_code="DB-MIG-FETCH-001",
            context=error_context
        )
    
    # Get list of migration files
    migrations_dir = os.path.join(os.path.dirname(__file__), "migrations")
    
    try:
        # Create migrations directory if it doesn't exist
        os.makedirs(migrations_dir, exist_ok=True)
    except OSError as e:
        error_context = ErrorContext(
            source="migrations.run_migrations",
            severity=ErrorSeverity.ERROR,
            timestamp=datetime.now(UTC),
            error_id=str(uuid4()),
            additional_data={"migrations_dir": migrations_dir, "error": str(e)}
        )
        raise DatabaseMigrationError(
            message=f"Failed to create migrations directory: {str(e)}",
            error_code="DB-MIG-DIR-002",
            context=error_context
        )
    
    # Import the migrations module to get files
    try:
        from app.database.migrations import get_migration_files, run_migration
    except ImportError as e:
        error_context = ErrorContext(
            source="migrations.run_migrations",
            severity=ErrorSeverity.CRITICAL,
            timestamp=datetime.now(UTC),
            error_id=str(uuid4()),
            additional_data={"error": str(e)}
        )
        raise DatabaseMigrationError(
            message=f"Failed to import migration utilities: {str(e)}",
            error_code="DB-MIG-IMPORT-001",
            context=error_context
        )
    
    migration_files = sorted([
        f for f in get_migration_files()
        if f.startswith("migration_") and f.endswith(".py")
    ])
    
    # Run pending migrations
    for migration_file in migration_files:
        if migration_file not in applied_migrations:
            try:
                # Run the migration using the new function
                run_migration(migration_file)
                
                # Record migration
                with engine.connect() as conn:
                    conn.execute(
                        text("INSERT INTO migrations (name) VALUES (:name)"),
                        {"name": migration_file}
                    )
                    conn.commit()
                
                print(f"Successfully applied migration: {migration_file}")
            except Exception as e:
                error_context = ErrorContext(
                    source="migrations.run_migrations",
                    severity=ErrorSeverity.CRITICAL,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "migration_file": migration_file,
                        "error": str(e)
                    }
                )
                raise DatabaseMigrationError(
                    message=f"Failed to apply migration {migration_file}: {str(e)}",
                    error_code="DB-MIG-APPLY-001",
                    context=error_context
                )

if __name__ == "__main__":
    run_migrations() 