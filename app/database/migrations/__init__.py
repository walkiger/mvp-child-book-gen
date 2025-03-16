"""
Migrations package for database schema changes.
"""

import os
import importlib.util
from pathlib import Path
from datetime import datetime
from app.database.migrations_utils import run_migrations as run_migrations_impl, create_migration_script as create_migration_script_impl

# Re-export these functions to maintain compatibility
def run_migrations():
    """Run database migrations."""
    return run_migrations_impl()

def create_migration_script():
    """Create a new migration script."""
    return create_migration_script_impl()

def get_migration_files():
    """
    Returns a list of all migration files in this directory.
    """
    migrations_dir = Path(__file__).parent
    migration_files = []
    
    for f in migrations_dir.glob("*.py"):
        if f.name != "__init__.py" and not f.name.startswith("_"):
            migration_files.append(f.name)
    
    return migration_files

def run_migration(migration_file):
    """
    Run a specific migration file.
    """
    try:
        print(f"Running migration: {migration_file}")
        # Get the full path to the migration file
        migrations_dir = Path(__file__).parent
        file_path = migrations_dir / migration_file
        
        # Import the module using the file path
        spec = importlib.util.spec_from_file_location(
            f"app.database.migrations.{migration_file[:-3]}", 
            file_path
        )
        migration_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration_module)
        
        # Call the migrate function
        if hasattr(migration_module, "migrate"):
            migration_module.migrate()
        else:
            print(f"Warning: {migration_file} does not have a migrate function")
            
    except Exception as e:
        print(f"Error running migration {migration_file}: {str(e)}")
        raise 