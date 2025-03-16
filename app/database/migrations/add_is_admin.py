"""
Migration script to add is_admin column to users table.
"""

import sqlite3
import os
from pathlib import Path

from app.config import settings

def migrate():
    """Add is_admin column to users table if it doesn't exist"""
    
    # Connect to the database
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "is_admin" not in columns:
            print("Adding is_admin column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT 0")
            print("Migration completed successfully.")
        else:
            print("The is_admin column already exists. Skipping migration.")
            
        conn.commit()
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        conn.rollback()
    finally:
        conn.close()
    
if __name__ == "__main__":
    migrate() 