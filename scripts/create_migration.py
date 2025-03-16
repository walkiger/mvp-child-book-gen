#!/usr/bin/env python
"""
Script to create a new database migration.
"""
import os
import sys

# Add parent directory to path to ensure imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.migrations import create_migration_script

if __name__ == "__main__":
    migration_path = create_migration_script()
    print(f"Created new migration at: {migration_path}")
    print("To run this migration, start the application or use the run_migrations.py script.") 