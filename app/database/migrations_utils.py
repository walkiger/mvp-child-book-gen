"""
Database migration utilities.
"""
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.database.models import Base

def create_migration_script():
    """Create a new migration script with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    migration_name = f"migration_{timestamp}.py"
    migration_path = os.path.join(os.path.dirname(__file__), "migrations", migration_name)
    
    os.makedirs(os.path.dirname(migration_path), exist_ok=True)
    
    template = f'''"""
Migration script created at {timestamp}
"""
from sqlalchemy import text
from sqlalchemy import create_engine
from app.database.models import Base
from app.config import settings

def migrate():
    """Run the migration."""
    # Create engine
    engine = create_engine(settings.DATABASE_URL)
    
    # Implement your migration here
    with engine.connect() as conn:
        # Example: Add a new column
        # conn.execute(text("ALTER TABLE your_table ADD COLUMN new_column VARCHAR"))
        
        # Commit the transaction
        conn.commit()
        print("Migration completed successfully")
'''
    
    with open(migration_path, "w") as f:
        f.write(template)
    
    print(f"Created migration script: {migration_path}")
    return migration_path

def run_migrations():
    """Run all pending migrations."""
    engine = create_engine(settings.DATABASE_URL)
    
    # Create migrations table if it doesn't exist
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS migrations (
                id INTEGER PRIMARY KEY,
                name VARCHAR NOT NULL,
                applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()
    
    # Get list of applied migrations
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM migrations"))
        applied_migrations = {row[0] for row in result}
    
    # Get list of migration files
    migrations_dir = os.path.join(os.path.dirname(__file__), "migrations")
    
    # Create migrations directory if it doesn't exist
    os.makedirs(migrations_dir, exist_ok=True)
    
    # Import the migrations module to get files
    from app.database.migrations import get_migration_files, run_migration
    
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
                print(f"Error applying migration {migration_file}: {str(e)}")
                sys.exit(1)

if __name__ == "__main__":
    run_migrations() 