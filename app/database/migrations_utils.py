"""
Database migration utilities.
"""
import os
import sys
from datetime import datetime, UTC
from uuid import uuid4
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from app.config import get_settings
from app.database.models import Base
from app.core.errors import DatabaseMigrationError, ErrorContext, ErrorSeverity

def create_migration_script():
    """Create a new migration script with timestamp."""
    try:
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
from app.config import get_settings
from app.core.errors import DatabaseMigrationError, ErrorContext, ErrorSeverity
from datetime import datetime, UTC
from uuid import uuid4

def migrate():
    """Run the migration."""
    try:
        # Create engine
        engine = create_engine(get_settings().DATABASE_URL)
        
        # Implement your migration here
        with engine.connect() as conn:
            # Example: Add a new column
            # conn.execute(text("ALTER TABLE your_table ADD COLUMN new_column VARCHAR"))
            
            # Commit the transaction
            conn.commit()
            print("Migration completed successfully")
    except SQLAlchemyError as e:
        error_context = ErrorContext(
            source="database.migrations.{timestamp}",
            severity=ErrorSeverity.ERROR,
            timestamp=datetime.now(UTC),
            error_id=str(uuid4()),
            additional_data={{"error": str(e)}}
        )
        raise DatabaseMigrationError(
            message=f"Failed to execute migration: {{str(e)}}",
            error_code="DATABASE-MIG-001",
            migration_name="{migration_name}",
            context=error_context
        ) from e
'''
        
        with open(migration_path, 'w') as f:
            f.write(template)
            
        print(f"Created migration script: {migration_name}")
        return migration_path
    except Exception as e:
        error_context = ErrorContext(
            source="database.migrations.create_script",
            severity=ErrorSeverity.ERROR,
            timestamp=datetime.now(UTC),
            error_id=str(uuid4()),
            additional_data={"error": str(e)}
        )
        raise DatabaseMigrationError(
            message=f"Failed to create migration script: {str(e)}",
            error_code="DATABASE-MIG-002",
            migration_name="create_script",
            context=error_context
        ) from e

def run_migrations():
    """Run all pending migrations."""
    try:
        # Create engine
        engine = create_engine(get_settings().DATABASE_URL)
        
        # Create all tables
        Base.metadata.create_all(engine)
        
        # Get list of migration files
        migrations_dir = os.path.join(os.path.dirname(__file__), "migrations")
        os.makedirs(migrations_dir, exist_ok=True)
        
        migration_files = sorted([
            f for f in os.listdir(migrations_dir)
            if f.startswith("migration_") and f.endswith(".py")
        ])
        
        # Run each migration
        for migration_file in migration_files:
            try:
                # Import and run migration
                sys.path.insert(0, migrations_dir)
                migration_module = __import__(migration_file[:-3])
                migration_module.migrate()
                sys.path.pop(0)
            except Exception as e:
                error_context = ErrorContext(
                    source=f"database.migrations.{migration_file}",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "migration_file": migration_file,
                        "error": str(e)
                    }
                )
                raise DatabaseMigrationError(
                    message=f"Failed to run migration {migration_file}: {str(e)}",
                    error_code="DATABASE-MIG-003",
                    migration_name=migration_file,
                    context=error_context
                ) from e
        
        print("All migrations completed successfully")
    except Exception as e:
        error_context = ErrorContext(
            source="database.migrations.run_migrations",
            severity=ErrorSeverity.ERROR,
            timestamp=datetime.now(UTC),
            error_id=str(uuid4()),
            additional_data={"error": str(e)}
        )
        raise DatabaseMigrationError(
            message=f"Failed to run migrations: {str(e)}",
            error_code="DATABASE-MIG-004",
            migration_name="run_migrations",
            context=error_context
        ) from e

if __name__ == "__main__":
    run_migrations() 