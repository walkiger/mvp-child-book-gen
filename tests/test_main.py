import pytest
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse
from app.main import app, read_root
from unittest.mock import patch, MagicMock, AsyncMock

@pytest.fixture
def client():
    return TestClient(app)

def test_read_root():
    """Test the root endpoint returns the expected message"""
    response = read_root()
    assert response == {
        "message": "Welcome to the MVP Child Book Generator API",
        "docs": "/docs",
    }

def test_root_endpoint(client):
    """Test the root endpoint via HTTP request"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to the MVP Child Book Generator API",
        "docs": "/docs",
    }

def test_cors_headers(client):
    """Test that CORS headers are properly set"""
    response = client.options(
        "/",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "access-control-allow-methods" in response.headers
    assert "GET" in response.headers["access-control-allow-methods"]

def test_non_api_routes_skip_rate_limiting(client):
    """Test that non-API routes skip rate limiting"""
    # Non-API routes should not be affected by rate limiting
    response = client.get("/")
    assert response.status_code == 200 