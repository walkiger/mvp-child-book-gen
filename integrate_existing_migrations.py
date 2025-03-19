"""
Script to integrate existing database migrations into Alembic.

This script:
1. Creates Alembic versions for existing migrations
2. Records them as applied
3. Sets up Alembic to work with future migrations
"""

import os
import sys
import re
import time
import importlib.util
import subprocess
from datetime import datetime
from typing import List, Tuple

# Constants
ALEMBIC_VERSIONS_DIR = os.path.join('alembic', 'versions')
MIGRATIONS_DIR = os.path.join('app', 'database', 'migrations')

def ensure_directories():
    """Ensure required directories exist"""
    if not os.path.exists(ALEMBIC_VERSIONS_DIR):
        print(f"Creating {ALEMBIC_VERSIONS_DIR} directory...")
        os.makedirs(ALEMBIC_VERSIONS_DIR)
        print("✓ Created successfully")
    else:
        print(f"✓ {ALEMBIC_VERSIONS_DIR} directory exists")

    if not os.path.exists(MIGRATIONS_DIR):
        print(f"Error: {MIGRATIONS_DIR} directory not found")
        sys.exit(1)
    else:
        print(f"✓ {MIGRATIONS_DIR} directory exists")

def get_migration_files() -> List[str]:
    """Get list of migration files sorted by creation time"""
    migration_files = []
    for filename in os.listdir(MIGRATIONS_DIR):
        if filename.endswith('.py') and not filename.startswith('__'):
            file_path = os.path.join(MIGRATIONS_DIR, filename)
            file_ctime = os.path.getctime(file_path)
            migration_files.append((filename, file_ctime))
    
    # Sort by creation time
    migration_files.sort(key=lambda x: x[1])
    return [f[0] for f in migration_files]

def process_migration(migration_file: str, prev_revision: str) -> Tuple[str, str]:
    """Process a migration file and return its revision ID and next revision ID"""
    print(f"\nProcessing migration: {migration_file}")
    
    # Import the migration module
    module_name = f"migration_{int(time.time())}"
    migration_path = os.path.join(MIGRATIONS_DIR, migration_file)
    
    try:
        spec = importlib.util.spec_from_file_location(module_name, migration_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as e:
        print(f"Error importing migration {migration_file}: {e}")
        return None, None
    
    # Generate revision ID
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    revision = f"{timestamp}_{migration_file[:-3]}"
    
    # Create Alembic version file
    version_filename = f"{revision}.py"
    version_path = os.path.join(ALEMBIC_VERSIONS_DIR, version_filename)
    
    print(f"Creating version file: {version_filename}")
    with open(version_path, 'w') as f:
        f.write(f"""\"\"\"Migration {migration_file}

Revision ID: {revision}
Revises: {prev_revision or ''}
Create Date: {datetime.now().isoformat()}
\"\"\"

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '{revision}'
down_revision = '{prev_revision}'
branch_labels = None
depends_on = None

def upgrade():
    {module.upgrade.__doc__ or '"""Pass"""'}
    {inspect.getsource(module.upgrade)}

def downgrade():
    {module.downgrade.__doc__ or '"""Pass"""'}
    {inspect.getsource(module.downgrade)}
""")
    
    return revision, version_filename

def main():
    """Main function to run the migration integration"""
    print("Integrating existing migrations into Alembic...")
    ensure_directories()
    
    migration_files = get_migration_files()
    if not migration_files:
        print("\nNo migration files found.")
        return
    
    print(f"\nFound {len(migration_files)} migration files:")
    for f in migration_files:
        print(f"  • {f}")
    
    prev_revision = None
    for migration_file in migration_files:
        revision, version_file = process_migration(migration_file, prev_revision)
        if revision:
            print(f"✓ Created {version_file}")
            prev_revision = revision
        else:
            print(f"✗ Failed to process {migration_file}")
    
    print("\nMigration integration complete!")

if __name__ == '__main__':
    main() 