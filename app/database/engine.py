# app/database/engine.py

"""
Database engine and session setup.
"""

from datetime import datetime, UTC
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from app.config import settings, get_settings
from app.core.errors.base import ErrorContext, ErrorSeverity
from app.core.errors.database import DatabaseConnectionError

try:
    # Get settings instance if None (test mode)
    current_settings = settings if settings is not None else get_settings()

    # Use the database_url property from settings
    DATABASE_URL = current_settings.database_url

    # Initialize the database engine and session
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
    SessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )
except SQLAlchemyError as e:
    error_context = ErrorContext(
        source="engine",
        severity=ErrorSeverity.CRITICAL,
        timestamp=datetime.now(UTC),
        error_id=str(uuid4()),
        additional_data={
            "database_url": DATABASE_URL if 'DATABASE_URL' in locals() else None,
            "error": str(e)
        }
    )
    raise DatabaseConnectionError(
        message=f"Failed to initialize database engine: {str(e)}",
        error_code="DB-ENGINE-001",
        context=error_context
    )
except Exception as e:
    error_context = ErrorContext(
        source="engine",
        severity=ErrorSeverity.CRITICAL,
        timestamp=datetime.now(UTC),
        error_id=str(uuid4()),
        additional_data={"error": str(e)}
    )
    raise DatabaseConnectionError(
        message=f"Unexpected error during engine initialization: {str(e)}",
        error_code="DB-ENGINE-002",
        context=error_context
    )
