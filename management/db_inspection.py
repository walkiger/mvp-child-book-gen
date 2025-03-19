"""
Database inspection utilities for examining and reporting on database structure and contents
"""

import os
import sys
import json
import sqlite3
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

from app.core.errors.base import ErrorContext, ErrorSeverity
from app.core.errors.management import (
    ManagementDatabaseError as DatabaseError,
    with_management_error_handling as with_error_handling
)
from app.core.logging import setup_logger

from .db_utils import DEFAULT_DB_PATH

# Setup logger
logger = setup_logger(
    name="management.db_inspection",
    level="INFO",
    log_file="logs/management.log"
)

def print_line(char="-", length=60):
    """Print a separator line with the specified character and length"""
    print(char * length)
    sys.stdout.flush()

def check_db_structure(db_path=None):
    """Check and display the structure of the database
    
    Args:
        db_path: Optional custom path for the database file
        
    Returns:
        True if successful, False otherwise
        
    Raises:
        FileNotFoundError: If the database file doesn't exist
    """
    print("=== DEBUG: Running check_db_structure() ===")
    sys.stdout.flush()
    
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    
    print("\nDATABASE STRUCTURE CHECK")
    print_line("=")
    print(f"Database path: {db_path}")
    sys.stdout.flush()
    
    if not os.path.exists(db_path):
        print(f"\nERROR: Database file not found at {db_path}")
        sys.stdout.flush()
        raise FileNotFoundError(f"Database file not found at {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        print(f"Tables found: {len(tables)}")
        sys.stdout.flush()
        
        # Process each table
        for table_tuple in tables:
            table_name = table_tuple[0]
            print_line()
            print(f"TABLE: {table_name}")
            print_line()
            sys.stdout.flush()
            
            # Get table info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print("Columns:")
            for col in columns:
                col_id, name, type_name, notnull, default_val, pk = col
                constraints = []
                
                if pk:
                    constraints.append("PRIMARY KEY")
                if notnull:
                    constraints.append("NOT NULL")
                if default_val is not None:
                    constraints.append(f"DEFAULT {default_val}")
                    
                constraints_str = " ".join(constraints)
                formatted_line = f"  - {name}: {type_name}"
                if constraints_str:
                    formatted_line += f" ({constraints_str})"
                print(formatted_line)
            sys.stdout.flush()
            
            # Row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"\nRow count: {count}")
            sys.stdout.flush()
        
        print_line("=")
        print("Database structure check completed.")
        sys.stdout.flush()
        conn.close()
        return True
    except Exception as e:
        print(f"Error checking database structure: {str(e)}")
        sys.stdout.flush()
        return False

@with_error_handling
def explore_db_contents(db_path=None):
    """Explore and display the contents of the database
    
    Args:
        db_path: Optional custom path for the database file
    """
    print("=== DEBUG: Running explore_db_contents() ===")
    sys.stdout.flush()
    
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    
    print("\nDATABASE CONTENTS EXPLORER")
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
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("\nTables in database:")
        for table in tables:
            table_name = table[0]
            print(f"- {table_name}")
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            print(f"  Columns in {table_name}:")
            for col in columns:
                print(f"    {col[1]} ({col[2]})")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  Row count: {count}")
            sys.stdout.flush()
        
        # Check for images table
        print("\n--- DETAILS FOR SPECIFIC TABLES ---")
        try:
            cursor.execute("SELECT COUNT(*) FROM images")
            image_count = cursor.fetchone()[0]
            print("\n=== IMAGES TABLE ===")
            print(f"Total images: {image_count}")
            sys.stdout.flush()
            
            if image_count > 0:
                # Show image information (limit to 5)
                try:
                    cursor.execute("""
                        SELECT id, user_id, filename, path, type, width, height, created_at
                        FROM images LIMIT 5
                    """)
                    rows = cursor.fetchall()
                    for row in rows:
                        print(f"  Image ID: {row['id']}")
                        print(f"  User ID: {row['user_id']}")
                        print(f"  Filename: {row['filename']}")
                        print(f"  Path: {row['path']}")
                        print(f"  Type: {row['type']}")
                        print(f"  Dimensions: {row['width']}x{row['height']}")
                        print(f"  Created At: {row['created_at']}")
                        print()
                    sys.stdout.flush()
                except sqlite3.OperationalError as e:
                    print(f"  Error accessing image data: {str(e)}")
                    sys.stdout.flush()
        except sqlite3.OperationalError:
            print("Images table not found or has different structure.")
            sys.stdout.flush()
        
        # Check characters table
        try:
            cursor.execute("SELECT COUNT(*) FROM characters")
            char_count = cursor.fetchone()[0]
            print("\n=== CHARACTERS TABLE ===")
            print(f"Total characters: {char_count}")
            sys.stdout.flush()
            
            if char_count > 0:
                # Show character information (limit to 5)
                try:
                    cursor.execute("""
                        SELECT id, story_id, name, description, image_url, created_at
                        FROM characters LIMIT 5
                    """)
                    rows = cursor.fetchall()
                    for row in rows:
                        print(f"  Character ID: {row['id']}")
                        print(f"  Story ID: {row['story_id']}")
                        print(f"  Name: {row['name']}")
                        print(f"  Description: {row['description']}")
                        print(f"  Image URL: {row['image_url']}")
                        print(f"  Created At: {row['created_at']}")
                        print()
                    sys.stdout.flush()
                except sqlite3.OperationalError as e:
                    print(f"  Error accessing character data: {str(e)}")
                    sys.stdout.flush()
        except sqlite3.OperationalError:
            print("Characters table not found or has different structure.")
            sys.stdout.flush()
        
        print_line("=")
        print("Database exploration completed.")
        sys.stdout.flush()
        conn.close()
        return True
    except Exception as e:
        print(f"Error exploring database: {str(e)}")
        sys.stdout.flush()
        raise DatabaseError("Failed to explore database contents", 
                          db_path=db_path,
                          severity=ErrorSeverity.ERROR, 
                          details=str(e))

@with_error_handling
def dump_db_to_file(db_path=None, output_file="db_dump.txt"):
    """Dump database structure and contents to a file
    
    Args:
        db_path: Optional custom path for the database file
        output_file: Path to the output file
    """
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    
    print(f"\nDUMPING DATABASE TO FILE: {output_file}")
    print_line("=")
    print(f"Database path: {db_path}")
    sys.stdout.flush()
    
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        sys.stdout.flush()
        raise DatabaseError("Database file not found", db_path=db_path, 
                          severity=ErrorSeverity.ERROR)
    
    try:
        # Redirect stdout to a file
        original_stdout = sys.stdout
        with open(output_file, 'w') as f:
            sys.stdout = f
            
            print(f"DATABASE DUMP FOR: {db_path}")
            print(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print_line("=")
            
            # Execute structure check with output going to file
            check_db_structure(db_path)
            
            # Execute content exploration with output going to file
            explore_db_contents(db_path)
            
            print("\nEND OF DATABASE DUMP")
        
        # Restore stdout
        sys.stdout = original_stdout
        
        print(f"Database dump completed. Output written to {output_file}")
        sys.stdout.flush()
        return True
    except Exception as e:
        # Restore stdout in case of error
        sys.stdout = original_stdout
        print(f"Error dumping database to file: {str(e)}")
        sys.stdout.flush()
        raise DatabaseError("Failed to dump database to file", 
                          db_path=db_path,
                          severity=ErrorSeverity.ERROR, 
                          details=str(e)) 