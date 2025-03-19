"""
Database session management for SQLAlchemy.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, UTC
from uuid import uuid4
from sqlalchemy.engine import Engine
from app.database.models import Base
from app.config import get_settings
from app.core.errors.base import ErrorContext, ErrorSeverity
from app.core.errors.database import DatabaseConnectionError, DatabaseInitializationError

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite connection to use UTC timezone."""
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA timezone='UTC'")
        cursor.close()
    except Exception as e:
        error_context = ErrorContext(
            source="session.set_sqlite_pragma",
            severity=ErrorSeverity.ERROR,
            timestamp=datetime.now(UTC),
            error_id=str(uuid4()),
            additional_data={"error": str(e)}
        )
        raise DatabaseConnectionError(
            message=f"Failed to set SQLite timezone pragma: {str(e)}",
            error_code="DB-CONN-001",
            context=error_context
        )

def get_engine():
    """Create SQLAlchemy engine."""
    try:
        engine = create_engine(
            get_settings().DATABASE_URL,
            connect_args={"check_same_thread": False}
        )
        return engine
    except SQLAlchemyError as e:
        error_context = ErrorContext(
            source="session.get_engine",
            severity=ErrorSeverity.CRITICAL,
            timestamp=datetime.now(UTC),
            error_id=str(uuid4()),
            additional_data={"error": str(e)}
        )
        raise DatabaseConnectionError(
            message=f"Failed to create database engine: {str(e)}",
            error_code="DB-CONN-002",
            context=error_context
        )
    except Exception as e:
        error_context = ErrorContext(
            source="session.get_engine",
            severity=ErrorSeverity.CRITICAL,
            timestamp=datetime.now(UTC),
            error_id=str(uuid4()),
            additional_data={"error": str(e)}
        )
        raise DatabaseConnectionError(
            message=f"Unexpected error creating database engine: {str(e)}",
            error_code="DB-CONN-003",
            context=error_context
        )

# Create engine and session factory
try:
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    error_context = ErrorContext(
        source="session",
        severity=ErrorSeverity.CRITICAL,
        timestamp=datetime.now(UTC),
        error_id=str(uuid4()),
        additional_data={"error": str(e)}
    )
    raise DatabaseConnectionError(
        message=f"Failed to create session factory: {str(e)}",
        error_code="DB-CONN-003",
        context=error_context
    )

def init_db():
    """Initialize database by creating all tables."""
    try:
        Base.metadata.create_all(bind=engine)
    except SQLAlchemyError as e:
        error_context = ErrorContext(
            source="session.init_db",
            severity=ErrorSeverity.CRITICAL,
            timestamp=datetime.now(UTC),
            error_id=str(uuid4()),
            additional_data={"error": str(e)}
        )
        raise DatabaseInitializationError(
            message=f"Failed to initialize database: {str(e)}",
            error_code="DB-INIT-001",
            context=error_context
        )

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        error_context = ErrorContext(
            source="session.get_db",
            severity=ErrorSeverity.ERROR,
            timestamp=datetime.now(UTC),
            error_id=str(uuid4()),
            additional_data={"error": str(e)}
        )
        raise DatabaseConnectionError(
            message=f"Database session error: {str(e)}",
            error_code="DB-CONN-004",
            context=error_context
        )
    finally:
        db.close() 