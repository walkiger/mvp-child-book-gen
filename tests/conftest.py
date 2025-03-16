"""
Pytest configuration file for the Child Book Generator MVP tests.

This file contains fixtures and configuration for the test suite.
"""

import os
import sys
import tempfile
import pytest
import sqlite3
import logging
import asyncio
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from fastapi.middleware.cors import CORSMiddleware

# Add parent directory to path to allow importing from root modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.models import Base, User, Character, Story, Image
from app.config import Settings
from app.database.session import get_db
from app import main
from utils.error_handling import (
    BaseError, DatabaseError, ServerError, ConfigError, 
    ResourceError, InputError, ImageError, ErrorSeverity,
    with_error_handling
)
from management.errors import ProcessError
from app.core.auth import get_password_hash


@pytest.fixture
def temp_db_path():
    """
    Create a temporary database file for testing.
    
    Yields:
        str: Path to the temporary database file
    """
    # Create a temporary file
    temp_fd, temp_path = tempfile.mkstemp()
    yield temp_path
    
    # Clean up after test
    os.close(temp_fd)
    os.unlink(temp_path)


@pytest.fixture
def temp_dir():
    """
    Create a temporary directory for testing.
    
    Yields:
        str: Path to the temporary directory
    """
    # Create a temporary directory
    temp_path = tempfile.mkdtemp()
    yield temp_path
    
    # Clean up after test
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def empty_db(temp_db_path):
    """
    Create an empty SQLite database for testing.
    
    Args:
        temp_db_path: Path to temporary database file (from fixture)
        
    Returns:
        str: Path to the initialized empty database
    """
    # Create an empty database
    conn = sqlite3.connect(temp_db_path)
    conn.close()
    return temp_db_path


@pytest.fixture
def mock_logger():
    """
    Create a mock logger for testing.
    
    Returns:
        MagicMock: A mock logger object
    """
    logger = MagicMock()
    yield logger


@pytest.fixture
def disable_logging():
    """
    Temporarily disable logging during tests.
    """
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


@pytest.fixture
def error_factory():
    """
    Create different types of management errors for testing.
    
    Returns:
        function: Factory function that creates error instances
    """
    def _create_error(error_type=ManagementError, message="Test error", 
                     severity=ErrorSeverity.ERROR, **kwargs):
        """
        Create an error instance of the specified type.
        
        Args:
            error_type: Error class to instantiate (default: ManagementError)
            message: Error message (default: "Test error")
            severity: Error severity level (default: ERROR)
            **kwargs: Additional arguments to pass to the error constructor
            
        Returns:
            Error instance of the specified type
        """
        return error_type(message, severity=severity, **kwargs)
    
    return _create_error


@pytest.fixture
def test_error_handling_function():
    """
    Provide a decorated function that raises exceptions for testing error handling.
    
    Returns:
        function: Test function with error handling decorator
    """
    @with_error_handling
    def test_function(exception_type=None, exit_on_error=False, 
                     log_level=logging.ERROR, raise_error=False,
                     error_message="Test error condition"):
        """
        Test function that raises exceptions based on input.
        
        Args:
            exception_type: Type of exception to raise
            exit_on_error: Whether to exit on error
            log_level: Log level to use
            raise_error: Whether to re-raise the error after handling
            error_message: Message for the raised error
            
        Returns:
            bool: True if no exception was raised, False otherwise
        """
        if exception_type:
            if issubclass(exception_type, ManagementError):
                raise exception_type(error_message)
            else:
                raise exception_type(error_message)
        return True
    
    return test_function


@pytest.fixture
def sqlite_memory_db():
    """
    Create an in-memory SQLite database with the application schema.
    
    Yields:
        Session: SQLAlchemy session connected to in-memory database
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def run_in_temp_dir():
    """
    Run a test function in a temporary directory.
    
    Yields:
        str: Path to the temporary directory
    """
    original_dir = os.getcwd()
    temp_dir = tempfile.mkdtemp()
    
    os.chdir(temp_dir)
    try:
        yield temp_dir
    finally:
        os.chdir(original_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def test_settings():
    """
    Create test settings with default values.
    
    Returns:
        Settings: Test settings object
    """
    return Settings(
        DATABASE_URL="sqlite:///:memory:",
        API_PORT=8001,
        DEBUG_MODE=True,
        LOG_LEVEL="INFO",
        API_KEY="test_api_key",
        OPENAI_API_KEY="test_openai_key"
    )


@pytest.fixture
def test_db_engine():
    """
    Create a test database engine.
    
    Yields:
        Engine: SQLAlchemy engine connected to in-memory database
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_db_session(test_db_engine):
    """
    Create a test database session.
    
    Args:
        test_db_engine: Test database engine (from fixture)
        
    Yields:
        Session: SQLAlchemy session for testing
    """
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def override_get_db(test_db_session):
    """
    Override the get_db dependency for testing.
    
    Args:
        test_db_session: Test database session (from fixture)
        
    Returns:
        function: Dependency function that returns the test session
    """
    def _get_test_db():
        try:
            yield test_db_session
        finally:
            pass
    
    return _get_test_db


@pytest.fixture
def test_app(override_get_db):
    """
    Create a FastAPI test application with the same routes as the main app.
    
    Args:
        override_get_db: Function that returns a test database session
        
    Returns:
        FastAPI: FastAPI application for testing
    """
    from app.api.auth import router as auth_router
    from app.api.characters import router as characters_router
    from app.api.stories import router as stories_router
    from app.api.images import router as images_router
    
    app = FastAPI(title="Test API")
    
    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include the same routers as the main app
    app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
    app.include_router(characters_router, prefix="/api/characters", tags=["characters"])
    app.include_router(stories_router, prefix="/api/stories", tags=["stories"])
    app.include_router(images_router, prefix="/api/images", tags=["images"])
    
    # Add root endpoint
    @app.get("/")
    def read_root():
        return {
            "message": "Welcome to the MVP Child Book Generator API",
            "docs": "/docs",
        }
    
    # Override the db dependency
    app.dependency_overrides[get_db] = override_get_db
    
    return app


@pytest.fixture
def test_client(test_app):
    """
    Create a TestClient for the FastAPI application.
    
    Args:
        test_app: FastAPI application
        
    Returns:
        TestClient: Test client for the application
    """
    return TestClient(test_app)


# -----------------------------------------------------------------------------
# Model Test Helpers
# -----------------------------------------------------------------------------

@pytest.fixture
def create_test_user(test_db_session):
    """
    Create a test user for testing.
    
    Args:
        test_db_session: SQLAlchemy session
        
    Returns:
        Function: Function to create a test user
    """
    def _create_user(username="testuser", email="test@example.com", password="password123"):
        password_hash = get_password_hash(password)
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            first_name="Test",
            last_name="User"
        )
        test_db_session.add(user)
        test_db_session.commit()
        test_db_session.refresh(user)
        return user
    
    return _create_user


@pytest.fixture
def create_test_character(test_db_session):
    """
    Create a test character for testing.
    
    Args:
        test_db_session: SQLAlchemy session
        
    Returns:
        Function: Function to create a test character
    """
    def _create_character(user_id, name="Test Character", traits=None):
        if traits is None:
            traits = {"age": 10, "personality": "friendly"}
        
        character = Character(
            user_id=user_id,
            name=name,
            traits=traits,
            image_prompt="A friendly character"
        )
        test_db_session.add(character)
        test_db_session.commit()
        return character
    
    return _create_character


@pytest.fixture
def create_test_story(test_db_session):
    """
    Create a test story for testing.
    
    Args:
        test_db_session: SQLAlchemy session
        
    Returns:
        Function: Function to create a test story
    """
    def _create_story(user_id, character_id, title="Test Story", age_group="3-5"):
        story = Story(
            user_id=user_id,
            character_id=character_id,
            title=title,
            content={
                "pages": [
                    {"text": "Once upon a time...", "image_id": None},
                    {"text": "The end.", "image_id": None}
                ]
            },
            age_group=age_group,
            page_count=2,
            moral_lesson="kindness",
            story_tone="whimsical"
        )
        test_db_session.add(story)
        test_db_session.commit()
        return story
    
    return _create_story


@pytest.fixture
def create_test_image(test_db_session):
    """
    Create a test image for testing.
    
    Args:
        test_db_session: SQLAlchemy session
        
    Returns:
        Function: Function to create a test image
    """
    def _create_image(story_id, character_id):
        image = Image(
            story_id=story_id,
            character_id=character_id,
            image_data=b"test_image_data",
            image_format="png",
            dalle_version="dall-e-3"
        )
        test_db_session.add(image)
        test_db_session.commit()
        return image
    
    return _create_image


@pytest.fixture
def auth_headers():
    """
    Create auth headers for API testing.
    
    Returns:
        Dict: Auth headers for API requests
    """
    return {
        "Authorization": "Bearer test_token",
        "Content-Type": "application/json"
    } 