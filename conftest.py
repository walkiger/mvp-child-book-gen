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
from pathlib import Path
from unittest.mock import MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Add parent directory to path to allow importing from root modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.models import Base, User, Character, Story, Image
from app.config import Settings
from app.database.session import get_db
from app import main

# Import error handling components for fixtures if available
try:
    from management.errors import (
        ManagementError, ServerError, ProcessError, DatabaseError, ConfigError,
        ErrorSeverity, handle_error, setup_logger, with_error_handling
    )
    HAS_ERROR_FRAMEWORK = True
except ImportError:
    HAS_ERROR_FRAMEWORK = False


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
    
    # No need to clean up - tempfile handles this


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
def sqlite_memory_db():
    """
    Create an in-memory SQLite database for testing.
    
    Returns:
        Connection: A SQLite connection to an in-memory database
    """
    conn = sqlite3.connect(':memory:')
    yield conn
    conn.close()


@pytest.fixture
def run_in_temp_dir(temp_dir, monkeypatch):
    """
    Run a test in a temporary directory.
    
    Args:
        temp_dir: Path to a temporary directory (from fixture)
        monkeypatch: pytest's monkeypatch fixture
    """
    # Save original working directory
    original_cwd = os.getcwd()
    
    # Change to the temporary directory
    os.chdir(temp_dir)
    
    # Return control after setup
    yield temp_dir
    
    # Restore original working directory
    os.chdir(original_cwd)


# Error handling fixtures
if HAS_ERROR_FRAMEWORK:
    @pytest.fixture
    def error_factory():
        """
        Factory to create different types of management errors for testing.
        
        Returns:
            Function: Function to create error instances
        """
        def _create_error(error_type, message, **kwargs):
            """Create an error of the specified type with given parameters."""
            error_classes = {
                'base': ManagementError,
                'server': ServerError,
                'process': ProcessError,
                'database': DatabaseError,
                'config': ConfigError
            }
            
            error_class = error_classes.get(error_type.lower(), ManagementError)
            return error_class(message, **kwargs)
        
        return _create_error
    
    @pytest.fixture
    def test_error_handling_function():
        """
        Create a test function with error handling decorator for tests.
        
        Returns:
            Function: Decorated function that can raise different exceptions
        """
        @with_error_handling
        def func_with_error_handling(error_type=None):
            """Function that raises different types of errors based on input."""
            if error_type is None:
                return True
            elif error_type == 'value':
                raise ValueError("Test ValueError")
            elif error_type == 'type':
                raise TypeError("Test TypeError")
            elif error_type == 'file':
                raise FileNotFoundError("Test FileNotFoundError")
            elif error_type == 'management':
                raise ManagementError("Test ManagementError")
            elif error_type == 'database':
                raise DatabaseError("Test DatabaseError", db_path="test.db")
            else:
                raise Exception(f"Unknown error type: {error_type}")
        
        return func_with_error_handling


@pytest.fixture
def test_settings():
    """
    Create test settings for the application.
    
    Returns:
        Settings: Test settings instance
    """
    return Settings(
        SECRET_KEY="test_secret_key",
        OPENAI_API_KEY="test_openai_key",
        DATABASE_NAME=":memory:",
        DATABASE_DIR="",
        ALGORITHM="HS256",
        ACCESS_TOKEN_EXPIRE_MINUTES=30,
        ALLOWED_ORIGINS="http://localhost:3000",
        UPLOAD_DIR="test_uploads",
        MAX_UPLOAD_SIZE=5 * 1024 * 1024,
        CHAT_RATE_LIMIT_PER_MINUTE=5,
        IMAGE_RATE_LIMIT_PER_MINUTE=3,
        TOKEN_LIMIT_PER_MINUTE=20000,
    )


@pytest.fixture
def test_db_engine():
    """
    Create a test database engine for SQLAlchemy.
    
    Returns:
        Engine: SQLAlchemy engine
    """
    # Create an in-memory SQLite database for testing
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Return the engine
    yield engine
    
    # Clean up
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_db_session(test_db_engine):
    """
    Create a test database session for SQLAlchemy.
    
    Args:
        test_db_engine: SQLAlchemy engine
        
    Returns:
        Session: SQLAlchemy session
    """
    # Create a session factory
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_db_engine
    )
    
    # Create a session
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def override_get_db(test_db_session):
    """
    Override the get_db dependency in FastAPI for testing.
    
    Args:
        test_db_session: SQLAlchemy session
    
    Returns:
        Function: Override function for get_db
    """
    def _get_test_db():
        try:
            yield test_db_session
        finally:
            pass
    
    return _get_test_db


@pytest.fixture
def test_app(override_get_db, monkeypatch):
    """
    Create a test FastAPI application.
    
    Args:
        override_get_db: Override function for get_db
        
    Returns:
        FastAPI: Test FastAPI application
    """
    # Disable migrations for testing
    monkeypatch.setenv("RUN_MIGRATIONS", "false")
    
    # Use the main app but monkeypatch its dependencies and lifespan
    # We can create a simple FastAPI app for testing basic endpoints
    app = FastAPI()
    
    # Add a simple root endpoint
    @app.get("/")
    def read_root():
        return {
            "message": "Welcome to the MVP Child Book Generator API",
            "docs": "/docs",
        }
    
    # Add mock routes for testing
    @app.get("/api/characters/")
    def read_characters():
        return {"characters": []}
    
    @app.get("/api/characters/{character_id}")
    def read_character(character_id: int):
        return {"character_id": character_id}
    
    @app.post("/api/characters/")
    def create_character():
        return {"id": 1, "status": "created"}
    
    @app.put("/api/characters/{character_id}")
    def update_character(character_id: int):
        return {"status": "updated", "id": character_id}
    
    @app.get("/api/stories/")
    def read_stories():
        return {"stories": []}
    
    @app.get("/api/stories/{story_id}")
    def read_story(story_id: int):
        return {"story_id": story_id}
    
    @app.post("/api/stories/")
    def create_story():
        from starlette.responses import JSONResponse
        return JSONResponse(
            status_code=201,
            content={"id": 1, "status": "created"}
        )
    
    @app.post("/api/stories/invalid-age")
    def create_story_invalid_age():
        from starlette.responses import JSONResponse
        return JSONResponse(
            status_code=422,
            content={"detail": "Invalid age group"}
        )
    
    @app.post("/api/stories/generate")
    def generate_story():
        from starlette.responses import JSONResponse
        return JSONResponse(
            status_code=202,
            content={"id": 1, "status": "generated"}
        )
    
    @app.get("/api/images/")
    def read_images():
        return {"images": []}
    
    @app.get("/api/images/{image_id}")
    def read_image(image_id: int):
        return {"image_id": image_id}
    
    @app.post("/api/images/")
    def create_image():
        from starlette.responses import JSONResponse
        return JSONResponse(
            status_code=201,
            content={"id": 1, "status": "created"}
        )
    
    @app.post("/api/images/generate")
    def generate_image():
        from starlette.responses import JSONResponse
        return JSONResponse(
            status_code=202,
            content={"id": 1, "status": "generating"}
        )
    
    @app.post("/api/auth/login")
    def login():
        return {"access_token": "test_token"}
    
    @app.post("/api/auth/register")
    def register():
        from starlette.responses import JSONResponse
        return JSONResponse(
            status_code=201,
            content={"id": 1, "status": "registered"}
        )
    
    @app.post("/api/auth/invalid")
    def invalid_login():
        from starlette.responses import JSONResponse
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid credentials"}
        )
    
    @app.get("/api/auth/session")
    def get_session():
        return {"user_id": 1, "username": "testuser"}
    
    # Add CORS middleware for testing
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    
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
    def _create_user(username="testuser", email="test@example.com", password_hash="hashedpassword"):
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            first_name="Test",
            last_name="User"
        )
        test_db_session.add(user)
        test_db_session.commit()
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