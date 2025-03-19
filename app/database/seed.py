# app/database/seed.py

"""
Database initialization and seeding.
"""

from datetime import datetime, UTC
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.database.models import Base
from app.database.session import init_db as init_session, get_db
from app.core.errors.base import ErrorContext, ErrorSeverity
from app.core.errors.database import DatabaseInitializationError, DatabaseSeedingError


def init_db() -> None:
    """
    Initialize the database by creating all tables.

    Raises:
        DatabaseInitializationError: If there's an error during database initialization.
    """
    try:
        # Initialize session factory
        init_session()
        
        # Get a session to create tables
        db = next(get_db())
        try:
            Base.metadata.create_all(bind=db.bind)
        except SQLAlchemyError as e:
            error_context = ErrorContext(
                source="seed.init_db",
                severity=ErrorSeverity.CRITICAL,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"error": str(e)}
            )
            raise DatabaseInitializationError(
                message=f"Failed to create database tables: {str(e)}",
                error_code="DB-INIT-002",
                context=error_context
            )
        finally:
            db.close()
    except Exception as e:
        error_context = ErrorContext(
            source="seed.init_db",
            severity=ErrorSeverity.CRITICAL,
            timestamp=datetime.now(UTC),
            error_id=str(uuid4()),
            additional_data={"error": str(e)}
        )
        raise DatabaseInitializationError(
            message=f"Failed to initialize database: {str(e)}",
            error_code="DB-INIT-003",
            context=error_context
        )


def seed_db(db: Session) -> None:
    """
    Seed the database with initial data.

    Args:
        db (Session): The database session to use.

    Raises:
        DatabaseSeedingError: If there's an error during database seeding.
    """
    try:
        # Add any initial data seeding here if needed
        pass
    except SQLAlchemyError as e:
        error_context = ErrorContext(
            source="seed.seed_db",
            severity=ErrorSeverity.ERROR,
            timestamp=datetime.now(UTC),
            error_id=str(uuid4()),
            additional_data={"error": str(e)}
        )
        raise DatabaseSeedingError(
            message=f"Failed to seed database: {str(e)}",
            error_code="DB-SEED-001",
            context=error_context
        )
    except Exception as e:
        error_context = ErrorContext(
            source="seed.seed_db",
            severity=ErrorSeverity.ERROR,
            timestamp=datetime.now(UTC),
            error_id=str(uuid4()),
            additional_data={"error": str(e)}
        )
        raise DatabaseSeedingError(
            message=f"Unexpected error during database seeding: {str(e)}",
            error_code="DB-SEED-002",
            context=error_context
        )
