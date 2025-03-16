"""
Script to integrate existing database migrations with Alembic.

This script:
1. Creates Alembic versions for existing migrations
2. Records them as applied
3. Sets up Alembic to work with future migrations
"""

import os
import re
import datetime
import importlib.util
import subprocess
from pathlib import Path

# Configuration
ALEMBIC_VERSIONS_DIR = os.path.join('alembic', 'versions')
MIGRATIONS_DIR = os.path.join('app', 'database', 'migrations')

def ensure_alembic_setup():
    """Ensure Alembic is set up correctly"""
    if not os.path.exists(ALEMBIC_VERSIONS_DIR):
        print(f"ERROR: Alembic versions directory not found at {ALEMBIC_VERSIONS_DIR}")
        print("Please run setup_project_env.py first to set up Alembic")
        return False
    return True

def get_existing_migrations():
    """Get list of existing migrations from the app/database/migrations directory"""
    if not os.path.exists(MIGRATIONS_DIR):
        print(f"No existing migrations found in {MIGRATIONS_DIR}")
        return []
    
    migration_files = [f for f in os.listdir(MIGRATIONS_DIR) 
                      if f.endswith('.py') and f != '__init__.py']
    
    return sorted(migration_files)

def extract_timestamp_from_migration(filename):
    """Extract timestamp from migration filename if possible"""
    match = re.search(r'migration_(\d{8})_(\d{6})', filename)
    if match:
        date_str = match.group(1)
        time_str = match.group(2)
        try:
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            hour = int(time_str[:2])
            minute = int(time_str[2:4])
            second = int(time_str[4:6])
            return datetime.datetime(year, month, day, hour, minute, second)
        except ValueError:
            pass
    
    # If no valid timestamp found, use file creation time
    file_path = os.path.join(MIGRATIONS_DIR, filename)
    file_ctime = os.path.getctime(file_path)
    return datetime.datetime.fromtimestamp(file_ctime)

def generate_alembic_version_for_migration(migration_file, timestamp):
    """Generate an Alembic version file for an existing migration"""
    # Generate a unique revision ID
    revision_id = timestamp.strftime('%Y%m%d%H%M%S')
    
    # Load the migration module to get its content
    migration_path = os.path.join(MIGRATIONS_DIR, migration_file)
    module_name = f"app.database.migrations.{migration_file[:-3]}"
    
    spec = importlib.util.spec_from_file_location(module_name, migration_path)
    migration_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration_module)
    
    # Extract upgrade and downgrade functions
    has_upgrade = hasattr(migration_module, 'upgrade')
    has_downgrade = hasattr(migration_module, 'downgrade')
    
    if not has_upgrade:
        print(f"WARNING: Migration {migration_file} has no upgrade function!")
        return None
    
    # Create alembic version file
    version_filename = f"{revision_id}_{migration_file[:-3]}.py"
    version_path = os.path.join(ALEMBIC_VERSIONS_DIR, version_filename)
    
    with open(version_path, 'w') as f:
        f.write(f'''"""
Migration converted from {migration_file}
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic
revision = '{revision_id}'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Call the original upgrade function with the required connection
    conn = op.get_bind()
    # The original function expects an engine, but bind should work
    from app.database.migrations.{migration_file[:-3]} import upgrade as original_upgrade
    original_upgrade(conn)

''')
        if has_downgrade:
            f.write('''
def downgrade():
    conn = op.get_bind()
    from app.database.migrations.{migration_file[:-3]} import downgrade as original_downgrade
    original_downgrade(conn)
''')
        else:
            f.write('''
def downgrade():
    # No downgrade function in original migration
    pass
''')
    
    print(f"Created Alembic version file: {version_filename}")
    return version_filename

def mark_migration_as_applied(version_file):
    """Mark a migration as applied in Alembic's version table"""
    # Extract revision ID from filename
    match = re.search(r'^(\w+)_', version_file)
    if not match:
        print(f"WARNING: Could not extract revision ID from {version_file}")
        return
    
    revision_id = match.group(1)
    
    # Run alembic stamp command
    cmd = ['alembic', 'stamp', revision_id]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"ERROR: Failed to mark migration {version_file} as applied")
        print(f"Error: {result.stderr}")
    else:
        print(f"Marked migration {version_file} as applied (revision {revision_id})")

def main():
    """Main function to integrate existing migrations with Alembic"""
    print("Integrating existing migrations with Alembic...")
    
    if not ensure_alembic_setup():
        return
    
    # Get existing migrations
    migrations = get_existing_migrations()
    
    if not migrations:
        print("No migrations to integrate")
        return
    
    print(f"Found {len(migrations)} existing migrations")
    
    # Process each migration
    for migration_file in migrations:
        print(f"\nProcessing migration: {migration_file}")
        
        # Extract timestamp
        timestamp = extract_timestamp_from_migration(migration_file)
        
        # Create Alembic version
        version_file = generate_alembic_version_for_migration(migration_file, timestamp)
        
        if version_file:
            # Mark as applied
            mark_migration_as_applied(version_file)
    
    print("\nMigration integration completed")
    print("\nYou can now use Alembic for future migrations:")
    print("  alembic revision --autogenerate -m \"your migration description\"")
    print("  alembic upgrade head")

if __name__ == "__main__":
    main() 