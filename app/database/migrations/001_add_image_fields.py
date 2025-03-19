"""
Migration to add new fields to the images table.
"""
from datetime import datetime, UTC
from uuid import uuid4
from sqlalchemy import text, create_engine
from sqlalchemy.exc import SQLAlchemyError
from app.config import get_settings
from app.core.errors import DatabaseMigrationError, ErrorContext

def migrate(engine):
    """Add image fields to the database."""
    try:
        with engine.connect() as conn:
            # Drop images_old table if it exists from a previous failed migration
            conn.execute(text("DROP TABLE IF EXISTS images_old"))
            conn.commit()

            # Check if images table exists
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='images'"))
            if result.fetchone():
                # Rename existing images table
                conn.execute(text("ALTER TABLE images RENAME TO images_old"))
                conn.commit()

            # Create new images table with updated schema
            conn.execute(text("""
                CREATE TABLE images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_data BLOB NOT NULL,
                    image_format VARCHAR(10) NOT NULL,
                    story_id INTEGER NOT NULL,
                    character_id INTEGER,
                    user_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (story_id) REFERENCES stories (id) ON DELETE CASCADE,
                    FOREIGN KEY (character_id) REFERENCES characters (id) ON DELETE SET NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """))
            conn.commit()

            # Copy data from old table if it exists
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='images_old'"))
            if result.fetchone():
                conn.execute(text("""
                    INSERT INTO images (
                        id, image_data, image_format, story_id, character_id, user_id, created_at, updated_at
                    )
                    SELECT 
                        id, data, format, story_id, character_id, user_id, created_at, updated_at
                    FROM images_old
                """))
                conn.commit()

                # Drop the old table
                conn.execute(text("DROP TABLE images_old"))
                conn.commit()
    except SQLAlchemyError as e:
        error_context = ErrorContext(
            source="migrations.001_add_image_fields.migrate",
            error_id=str(uuid4()),
            timestamp=datetime.now(UTC),
            error_code="DB-MIG-IMG-001",
            severity="ERROR",
            message=f"Database error during image fields migration: {str(e)}",
            additional_data={}
        )
        raise DatabaseMigrationError("Failed to migrate image fields", error_context) from e
    except Exception as e:
        error_context = ErrorContext(
            source="migrations.001_add_image_fields.migrate",
            error_id=str(uuid4()),
            timestamp=datetime.now(UTC),
            error_code="DB-MIG-IMG-002",
            severity="ERROR",
            message=f"Unexpected error during image fields migration: {str(e)}",
            additional_data={}
        )
        raise DatabaseMigrationError("Unexpected error during image fields migration", error_context) from e

def rollback(engine):
    """Rollback the migration."""
    try:
        with engine.connect() as conn:
            # Check if images_old table exists
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='images_old'"))
            if result.fetchone():
                # Drop new images table
                conn.execute(text("DROP TABLE IF EXISTS images"))
                conn.commit()
                
                # Rename old table back
                conn.execute(text("ALTER TABLE images_old RENAME TO images"))
                conn.commit()
            else:
                # Just drop the new table if no old table exists
                conn.execute(text("DROP TABLE IF EXISTS images"))
                conn.commit()
    except SQLAlchemyError as e:
        error_context = ErrorContext(
            source="migrations.001_add_image_fields.rollback",
            error_id=str(uuid4()),
            timestamp=datetime.now(UTC),
            error_code="DB-MIG-IMG-003",
            severity="ERROR",
            message=f"Database error during image fields rollback: {str(e)}",
            additional_data={}
        )
        raise DatabaseMigrationError("Failed to rollback image fields migration", error_context) from e
    except Exception as e:
        error_context = ErrorContext(
            source="migrations.001_add_image_fields.rollback",
            error_id=str(uuid4()),
            timestamp=datetime.now(UTC),
            error_code="DB-MIG-IMG-004",
            severity="ERROR",
            message=f"Unexpected error during image fields rollback: {str(e)}",
            additional_data={}
        )
        raise DatabaseMigrationError("Unexpected error during image fields rollback", error_context) from e