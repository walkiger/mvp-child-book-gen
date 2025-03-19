"""
Pytest configuration file for the Child Book Generator MVP tests.

This file contains fixtures and configuration for the test suite.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
import sys
import tempfile
import shutil
from unittest.mock import MagicMock, AsyncMock
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
import json
import uuid
from datetime import datetime, UTC
from sqlalchemy.engine import Engine

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

# Test settings
os.environ.update({
    "OPENAI_API_KEY": "sk-test_dummy_key",
    "DATABASE_URL": "sqlite:///:memory:",
    "UPLOAD_DIR": "./test_uploads",
    "JWT_SECRET_KEY": "test_secret_key",
    "RATE_LIMIT": "100/minute",
    "SECRET_KEY": "test_secret_key",
    "ALGORITHM": "HS256",
    "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
    "DATABASE_NAME": "test.db",
    "DATABASE_DIR": "./test_db",
    "ALLOWED_ORIGINS": "http://localhost:3000",
    "MAX_UPLOAD_SIZE": "5242880",
    "TESTING": "1",
    "RUN_MIGRATIONS": "false"  # Disable automatic migrations during tests
})

# Create test database directory
os.makedirs("./test_db", exist_ok=True)

# Now import app modules
from app.config import get_settings, Settings
from app.core.openai_client import get_openai_client
from app.database.models import Base, User
from app.core.security import get_password_hash
from app.api.auth import create_access_token, router as auth_router
from app.api.characters import router as character_router
from app.api.stories import router as story_router
from app.api.images import router as image_router
from app.database.session import get_db
from app.api.dependencies import get_current_user

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite connection to use UTC timezone."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA timezone='UTC'")
    cursor.close()

def get_test_settings():
    """Get test settings"""
    return Settings(testing=True)

def generate_unique_username():
    """Generate a unique username for testing."""
    return f"testuser_{uuid.uuid4().hex}"

def generate_unique_email():
    """Generate a unique email for testing."""
    return f"test_{uuid.uuid4().hex}@example.com"

@pytest.fixture
def temp_db_path():
    """Create a temporary database file."""
    db_fd, db_path = tempfile.mkstemp()
    yield db_path
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture(scope="session")
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.fixture(scope="session")
def test_settings(temp_dir):
    """Get test settings with temporary directories."""
    settings = get_settings()
    settings.database_dir = os.path.join(temp_dir, "test_db")
    settings.upload_dir = os.path.join(temp_dir, "test_uploads")
    return settings

@pytest.fixture(scope="function")
def test_db_engine():
    """Create a fresh test database engine for each test."""
    # Create an in-memory SQLite database for testing
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    return engine

@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create a new database session for a test."""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_db_engine
    )
    
    # Create a new session for the test
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture(scope="function")
def test_client(test_db_session):
    """Create a test client with a test database session."""
    from app.main import app

    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings] = get_test_settings

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def test_user(test_db_session):
    """Create a test user for authentication tests."""
    email = generate_unique_email()
    username = generate_unique_username()
    password_hash = get_password_hash("testpassword123")
    
    user = User(
        email=email,
        username=username,
        password_hash=password_hash,
        first_name="Test",
        last_name="User"
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def test_token(test_user):
    """Create a test token for a test user."""
    return create_access_token({"sub": test_user.email})

@pytest.fixture
def auth_headers(test_token):
    """Get authorization headers for testing."""
    return {"Authorization": f"Bearer {test_token}"}

class MockImageResponse:
    def __init__(self, url):
        self.url = url

class MockResponse:
    def __init__(self, status_code=200, content=b"test_image_data", headers=None):
        self.status_code = status_code
        self.content = content
        self.headers = headers or {"content-type": "image/png"}

class MockAsyncClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def get(self, url):
        return MockResponse()

@pytest.fixture
def mock_httpx_client(monkeypatch):
    """Mock httpx.AsyncClient for testing."""
    monkeypatch.setattr("httpx.AsyncClient", MockAsyncClient)
    return MockAsyncClient()

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    mock_client = MagicMock()

    # Mock story generation response
    mock_story_response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "title": "Test Story",
                        "pages": [
                            {
                                "text": "Once upon a time...",
                                "visual_description": "A happy scene with characters playing"
                            }
                        ]
                    })
                }
            }
        ]
    }

    # Mock image generation response
    mock_image_response = {
        "data": [
            {
                "url": "https://example.com/test.png"
            }
        ]
    }

    # Configure the mock responses
    mock_client.chat.completions.create = AsyncMock(return_value=mock_story_response)
    mock_client.images.generate = AsyncMock(return_value=mock_image_response)

    return mock_client

@pytest.fixture
def test_app(test_db_session, mock_openai_client):
    """Create a test FastAPI application."""
    app = FastAPI(
        title="Child Book Generator MVP",
        description="API for generating personalized children's books",
        version="1.0.0"
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Override dependencies
    def get_test_db():
        try:
            yield test_db_session
        finally:
            test_db_session.close()

    def get_test_openai_client():
        return mock_openai_client

    app.dependency_overrides[get_db] = get_test_db
    app.dependency_overrides[get_settings] = get_test_settings
    app.dependency_overrides[get_openai_client] = get_test_openai_client

    # Include routers
    app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
    app.include_router(character_router, prefix="/api/characters", tags=["characters"])
    app.include_router(story_router, prefix="/api/stories", tags=["stories"])
    app.include_router(image_router, prefix="/api/images", tags=["images"])

    @app.get("/")
    def root():
        return {
            "message": "Welcome to the MVP Child Book Generator API",
            "docs": "/docs"
        }

    return app

@pytest.fixture
def client(test_app):
    """Create a test client."""
    return TestClient(test_app)