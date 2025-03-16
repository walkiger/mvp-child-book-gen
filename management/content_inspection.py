"""
Content inspection utilities for examining character and image data
"""

import os
import sys
import json
import sqlite3
from pathlib import Path

from .db_utils import DEFAULT_DB_PATH
from .errors import with_error_handling, DatabaseError, ErrorSeverity

def print_line(char="-", length=80):
    """Print a separator line with the specified character and length"""
    print(char * length)
    sys.stdout.flush()

@with_error_handling
def check_characters(db_path=None):
    """Check and display character information from the database
    
    Args:
        db_path: Optional custom path for the database file
    """
    print("DEBUG: Starting check_characters()...")
    sys.stdout.flush()
    
    if db_path is None:
        db_path = DEFAULT_DB_PATH
        print(f"DEBUG: Using default DB path: {db_path}")
        sys.stdout.flush()
    
    print("\nCHARACTER INSPECTION")
    print_line("=")
    print(f"Database path: {db_path}")
    sys.stdout.flush()
    
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        sys.stdout.flush()
        raise DatabaseError("Database file not found", db_path=db_path, 
                          severity=ErrorSeverity.ERROR)
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check character table structure
        print_line()
        print("CHARACTERS TABLE STRUCTURE:")
        cursor.execute("PRAGMA table_info(characters)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col['name']} ({col['type']})")
        sys.stdout.flush()
        
        # Count characters
        print_line()
        cursor.execute("SELECT COUNT(*) FROM characters")
        count = cursor.fetchone()[0]
        print(f"TOTAL CHARACTERS: {count}")
        sys.stdout.flush()
        
        # Look at character records
        if count > 0:
            print_line()
            print("CHARACTER RECORDS (showing up to 5):")
            cursor.execute("""
                SELECT id, story_id, name, description, image_url, created_at 
                FROM characters LIMIT 5
            """)
            records = cursor.fetchall()
            
            for i, record in enumerate(records, 1):
                print(f"\nCHARACTER {i}:")
                print(f"  ID: {record['id']}")
                print(f"  Story ID: {record['story_id']}")
                print(f"  Name: {record['name']}")
                print(f"  Description: {record['description']}")
                print(f"  Image URL: {record['image_url']}")
                print(f"  Created At: {record['created_at']}")
                sys.stdout.flush()
        
        print_line("=")
        print("Character inspection completed.")
        sys.stdout.flush()
        conn.close()
        return True
    except Exception as e:
        print(f"Error checking characters: {str(e)}")
        sys.stdout.flush()
        raise DatabaseError("Failed to check character information", 
                          db_path=db_path,
                          severity=ErrorSeverity.ERROR, 
                          details=str(e))

@with_error_handling
def check_images(db_path=None):
    """Check and display image information from the database
    
    Args:
        db_path: Optional custom path for the database file
    """
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    
    print("\nIMAGE INSPECTION")
    print_line("=")
    print(f"Database path: {db_path}")
    sys.stdout.flush()
    
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        sys.stdout.flush()
        raise DatabaseError("Database file not found", db_path=db_path, 
                          severity=ErrorSeverity.ERROR)
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check images table structure
        print_line()
        print("IMAGES TABLE STRUCTURE:")
        cursor.execute("PRAGMA table_info(images)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col['name']} ({col['type']})")
        sys.stdout.flush()
        
        # Count images
        print_line()
        cursor.execute("SELECT COUNT(*) FROM images")
        count = cursor.fetchone()[0]
        print(f"TOTAL IMAGES: {count}")
        sys.stdout.flush()
        
        # Look at image records
        if count > 0:
            print_line()
            print("IMAGE RECORDS (showing up to 5):")
            cursor.execute("""
                SELECT id, user_id, filename, path, type, width, height, created_at
                FROM images LIMIT 5
            """)
            records = cursor.fetchall()
            
            for i, record in enumerate(records, 1):
                print(f"\nIMAGE {i}:")
                print(f"  ID: {record['id']}")
                print(f"  User ID: {record['user_id']}")
                print(f"  Filename: {record['filename']}")
                print(f"  Path: {record['path']}")
                print(f"  Type: {record['type']}")
                print(f"  Dimensions: {record['width']}x{record['height']}")
                print(f"  Created At: {record['created_at']}")
                sys.stdout.flush()
        
        # Check for image files existence
        if count > 0:
            print_line()
            print("CHECKING IMAGE FILES EXISTENCE:")
            cursor.execute("SELECT path FROM images LIMIT 10")
            paths = cursor.fetchall()
            
            for path_data in paths:
                path = path_data['path']
                if path and os.path.exists(path):
                    print(f"  ✅ File exists: {path}")
                else:
                    print(f"  ❌ File missing: {path}")
            sys.stdout.flush()
        
        print_line("=")
        print("Image inspection completed.")
        sys.stdout.flush()
        conn.close()
        return True
    except Exception as e:
        print(f"Error checking images: {str(e)}")
        sys.stdout.flush()
        raise DatabaseError("Failed to check image information", 
                          db_path=db_path,
                          severity=ErrorSeverity.ERROR, 
                          details=str(e)) 