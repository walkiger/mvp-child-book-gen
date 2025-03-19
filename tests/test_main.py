"""Tests for the main FastAPI application."""

from fastapi.testclient import TestClient
from app.main import app
from app.core.error_handling import setup_error_handlers
from fastapi import FastAPI, HTTPException

def test_root_endpoint():
    """Test the root endpoint returns the expected message."""
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Welcome to the Child Book Generator API"}

def test_health_check():
    """Test the health check endpoint returns healthy status."""
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

def test_error_handlers_setup():
    """Test that error handlers are properly set up."""
    # Create a new test app
    test_app = FastAPI()
    
    # Set up error handlers
    setup_error_handlers(test_app)
    
    # Verify that exception handlers are registered
    assert test_app.exception_handlers
    
    # Create test client
    client = TestClient(test_app)
    
    # Test 404 error
    response = client.get("/nonexistent")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "error_code" in data
    assert data["error_code"] == "NOT_FOUND"

def test_api_version_header():
    """Test that API version header is added to responses."""
    with TestClient(app) as client:
        response = client.get("/")
        assert "X-API-Version" in response.headers
        assert response.headers["X-API-Version"]

def test_cors_headers():
    """Test that CORS headers are properly set."""
    with TestClient(app) as client:
        response = client.options("/", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        })
        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" in response.headers
        assert "Access-Control-Allow-Methods" in response.headers
        assert "Access-Control-Allow-Headers" in response.headers

def test_error_handling_middleware():
    """Test that the error handling middleware catches unhandled errors."""
    from fastapi import APIRouter
    
    # Create a test router that raises an error
    router = APIRouter()
    @router.get("/test-error")
    async def test_error():
        raise RuntimeError("Test error")
    
    # Create a new test app with the router
    test_app = FastAPI()
    test_app.include_router(router)
    setup_error_handlers(test_app)
    
    # Test the error response
    client = TestClient(test_app)
    response = client.get("/test-error")
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Internal server error"