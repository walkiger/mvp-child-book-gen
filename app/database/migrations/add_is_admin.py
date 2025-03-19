"""
Migration script to add is_admin column to users table.
"""

import sqlite3
import os
from datetime import datetime, UTC
from uuid import uuid4
from app.config import get_settings
from app.core.errors import DatabaseMigrationError, ErrorContext

def migrate():
    """Add is_admin column to users table if it doesn't exist"""
    try:
        settings = get_settings()
        
        # Get database path from settings
        if settings.database_url.startswith("sqlite:///"):
            db_path = settings.database_url.replace("sqlite:///", "")
        else:
            db_path = os.path.join(settings.database_dir, settings.database_name)
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Check if the column already exists
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if "is_admin" not in columns:
                print("Adding is_admin column to users table...")
                cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0")
                print("Migration completed successfully.")
            else:
                print("The is_admin column already exists. Skipping migration.")
                
            conn.commit()
        except sqlite3.Error as e:
            error_context = ErrorContext(
                source="migrations.add_is_admin.migrate",
                error_id=str(uuid4()),
                timestamp=datetime.now(UTC),
                error_code="DB-MIG-ADMIN-001",
                severity="ERROR",
                message=f"Database error adding is_admin column: {str(e)}",
                additional_data={"db_path": db_path}
            )
            raise DatabaseMigrationError("Failed to add is_admin column", error_context) from e
        finally:
            conn.close()
    except Exception as e:
        if not isinstance(e, DatabaseMigrationError):
            error_context = ErrorContext(
                source="migrations.add_is_admin.migrate",
                error_id=str(uuid4()),
                timestamp=datetime.now(UTC),
                error_code="DB-MIG-ADMIN-002",
                severity="ERROR",
                message=f"Unexpected error during is_admin migration: {str(e)}",
                additional_data={"db_path": db_path}
            )
            raise DatabaseMigrationError("Unexpected error during is_admin migration", error_context) from e
        raise
    
if __name__ == "__main__":
    migrate() 