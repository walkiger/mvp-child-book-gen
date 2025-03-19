"""
Tests for the API endpoints.
"""
import pytest
import json
from fastapi.testclient import TestClient
from app.database.models import User
from app.core.security import get_password_hash
from tests.conftest import generate_unique_username


# Use the test_app fixture from conftest.py
@pytest.fixture
def client(test_app):
    """Create a test client for the FastAPI application."""
    return TestClient(test_app)


def test_root_endpoint(client):
    """Test if the root endpoint returns the correct welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to the MVP Child Book Generator API",
        "docs": "/docs"
    }


@pytest.fixture
def create_test_user(test_db_session):
    """Create a test user with the given credentials."""
    def _create_test_user(username, email, password):
        user = User(
            username=username,
            email=email,
            password_hash=get_password_hash(password),
            first_name="Test",
            last_name="User"
        )
        test_db_session.add(user)
        test_db_session.commit()
        test_db_session.refresh(user)
        return user
    return _create_test_user


def test_auth_endpoints_exist(client):
    """Test that auth endpoints exist."""
    # Login route should exist
    response = client.post("/api/auth/login")
    assert response.status_code == 422  # Should be a 422 error (Unprocessable Entity)
    
    # Register route should exist
    response = client.post("/api/auth/register")
    assert response.status_code == 422  # Should be a 422 error (Unprocessable Entity)
    
    # Me route should exist
    response = client.get("/api/auth/me")
    assert response.status_code == 401  # Should be a 401 error (Unauthorized)


def test_character_endpoints_exist(client):
    """Test that character endpoints exist."""
    # List characters route should exist
    response = client.get("/api/characters/")
    assert response.status_code == 401  # Should be a 401 error (Unauthorized)
    
    # Create character route should exist
    response = client.post("/api/characters/")
    assert response.status_code == 401  # Should be a 401 error (Unauthorized)
    
    # Get character route should exist
    response = client.get("/api/characters/1")
    assert response.status_code == 401  # Should be a 401 error (Unauthorized)
    
    # Update character route should exist
    response = client.put("/api/characters/1")
    assert response.status_code == 401  # Should be a 401 error (Unauthorized)
    
    # Delete character route should exist
    response = client.delete("/api/characters/1")
    assert response.status_code == 401  # Should be a 401 error (Unauthorized)


def test_story_endpoints_exist(client):
    """Test that story endpoints exist."""
    # List stories route should exist
    response = client.get("/api/stories/")
    assert response.status_code == 401  # Should be a 401 error (Unauthorized)
    
    # Create story route should exist
    response = client.post("/api/stories/")
    assert response.status_code == 401  # Should be a 401 error (Unauthorized)
    
    # Get story route should exist
    response = client.get("/api/stories/1")
    assert response.status_code == 401  # Should be a 401 error (Unauthorized)
    
    # Update story route should exist
    response = client.put("/api/stories/1")
    assert response.status_code == 401  # Should be a 401 error (Unauthorized)
    
    # Delete story route should exist
    response = client.delete("/api/stories/1")
    assert response.status_code == 401  # Should be a 401 error (Unauthorized)


def test_image_endpoints_exist(client):
    """Test that image endpoints exist and require authentication."""
    response = client.get("/api/images/1")
    assert response.status_code == 401  # Should be unauthorized
    assert "Unauthorized" in response.json()["message"]


def test_cors_headers(client):
    """Test that CORS headers are set correctly."""
    response = client.options("/api/characters/", headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET",
    })
    
    # Check that CORS headers are present in the response
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "access-control-allow-credentials" in response.headers
    assert response.headers["access-control-allow-credentials"] == "true"


class TestAuthAPI:
    """Tests for the authentication API endpoints."""
    
    @pytest.fixture(autouse=True)
    def setup_user(self, test_db_session, create_test_user):
        """Create a test user for authentication tests."""
        self.test_user = create_test_user(
            username=generate_unique_username(),
            email="auth_test@example.com",
            password="password123"
        )
    
    def test_register_user(self, client):
        """Test user registration."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "testpassword123",
                "username": generate_unique_username(),
                "first_name": "Test",
                "last_name": "User"
            }
        )
        assert response.status_code == 201
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"
    
    def test_login_user(self, client):
        """Test user login."""
        # First register a user
        username = generate_unique_username()
        register_response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "testpassword123",
                "username": username,
                "first_name": "Test",
                "last_name": "User"
            }
        )
        assert register_response.status_code == 201
        
        # Then login with the registered user
        response = client.post(
            "/api/auth/login",
            data={
                "username": "test@example.com",
                "password": "testpassword123"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"
    
    def test_invalid_login(self, client):
        """Test login with invalid credentials."""
        # Login with wrong credentials
        response = client.post(
            "/api/auth/login",
            data={
                "username": "wronguser",
                "password": "wrongpassword"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 401  # Should be a 401 error (Unauthorized)
        assert "Incorrect email or password" in response.json()["detail"]


class TestCharacterAPI:
    def test_create_character(self, client, auth_headers, mock_openai_client, mock_httpx_client):
        """Test creating a character."""
        # Create a new character
        response = client.post(
            "/api/characters/",
            json={
                "name": "New Character",
                "traits": ["age: 10", "personality: friendly"],
                "image_prompt": "A friendly character"
            },
            headers=auth_headers
        )
        assert response.status_code in [200, 201]
        assert "id" in response.json()
        assert response.json()["name"] == "New Character"
    
    def test_get_character(self, client, auth_headers, mock_openai_client, mock_httpx_client):
        """Test getting a character."""
        # First create a character
        create_response = client.post(
            "/api/characters/",
            json={
                "name": "Test Character",
                "traits": ["age: 10", "personality: friendly"],
                "image_prompt": "A friendly character"
            },
            headers=auth_headers
        )
        assert create_response.status_code in [200, 201]
        character_id = create_response.json()["id"]
        
        # Then get the character
        response = client.get(
            f"/api/characters/{character_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Test Character"
    
    def test_update_character(self, client, auth_headers, mock_openai_client, mock_httpx_client):
        """Test updating a character."""
        # First create a character
        create_response = client.post(
            "/api/characters/",
            json={
                "name": "Test Character",
                "traits": ["age: 10", "personality: friendly"],
                "image_prompt": "A friendly character"
            },
            headers=auth_headers
        )
        assert create_response.status_code in [200, 201]
        character_id = create_response.json()["id"]
        
        # Then update the character
        response = client.put(
            f"/api/characters/{character_id}",
            json={
                "name": "Updated Character",
                "traits": ["age: 11", "personality: brave"],
                "image_prompt": "A brave character"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["id"] == character_id
        assert response.json()["name"] == "Updated Character"
    
    @pytest.mark.parametrize("traits", [
        ["age: 8", "personality: shy"],
        ["age: 10", "personality: outgoing"],
        ["age: 12", "personality: creative"]
    ])
    def test_character_with_different_traits(self, client, auth_headers, mock_openai_client, mock_httpx_client, traits):
        """Test creating characters with different traits."""
        response = client.post(
            "/api/characters/",
            json={
                "name": "Character with Traits",
                "traits": traits,
                "image_prompt": "A character with specific traits"
            },
            headers=auth_headers
        )
        assert response.status_code in [200, 201]
        assert "id" in response.json()
        assert response.json()["traits"] == traits


class TestStoryAPI:
    def test_create_story(self, client, auth_headers, mock_openai_client, mock_httpx_client):
        """Test creating a story."""
        # First create a character
        character_response = client.post(
            "/api/characters/",
            json={
                "name": "Story Character",
                "traits": ["age: 10", "personality: friendly"],
                "image_prompt": "A friendly character"
            },
            headers=auth_headers
        )
        assert character_response.status_code in [200, 201]
        character_id = character_response.json()["id"]
        
        # Then create a story
        response = client.post(
            "/api/stories/",
            json={
                "title": "Test Story",
                "character_id": character_id,
                "age_group": "3-5",
                "story_tone": "whimsical",
                "moral_lesson": "kindness",
                "page_count": 3
            },
            headers=auth_headers
        )
        assert response.status_code == 201
        assert response.json()["title"] == "Test Story"
    
    @pytest.mark.parametrize("age_group,expected_status", [
        ("3-5", 201),
        ("6-8", 201),
        ("9-12", 201),
        ("invalid-age", 422)
    ])
    def test_create_story_with_different_age_groups(self, client, auth_headers, mock_openai_client, mock_httpx_client, age_group, expected_status):
        """Test creating stories with different age groups."""
        # First create a character
        char_response = client.post(
            "/api/characters/",
            json={
                "name": "Story Character",
                "traits": ["age: 10", "personality: friendly"],
                "image_prompt": "A friendly character"
            },
            headers=auth_headers
        )
        assert char_response.status_code in [200, 201]
        character_id = char_response.json()["id"]
        
        # Then create a story
        response = client.post(
            "/api/stories/",
            json={
                "title": "Test Story",
                "character_id": character_id,
                "age_group": age_group,
                "story_tone": "adventurous",
                "moral_lesson": "courage",
                "page_count": 5
            },
            headers=auth_headers
        )
        assert response.status_code == expected_status
        if expected_status == 201:
            assert "id" in response.json()
            assert response.json()["age_group"] == age_group
    
    def test_generate_story(self, client, auth_headers, mock_openai_client, mock_httpx_client):
        """Test generating a story."""
        # First create a character
        character_response = client.post(
            "/api/characters/",
            json={
                "name": "Story Character",
                "traits": ["age: 10", "personality: friendly"],
                "image_prompt": "A friendly character"
            },
            headers=auth_headers
        )
        assert character_response.status_code in [200, 201]
        character_id = character_response.json()["id"]
        
        # Then generate a story
        response = client.post(
            "/api/stories/generate",
            json={
                "title": "Generated Story",
                "character_id": character_id,
                "age_group": "3-5",
                "story_tone": "whimsical",
                "moral_lesson": "kindness",
                "page_count": 3
            },
            headers=auth_headers
        )
        assert response.status_code == 201
        assert "content" in response.json()


class TestImageAPI:
    def test_generate_image(self, client, auth_headers, mock_openai_client, mock_httpx_client):
        """Test generating an image."""
        # Mock OpenAI response
        mock_openai_client.images.generate.return_value = {
            "data": [{"url": "https://example.com/test.png"}]
        }

        response = client.post(
            "/api/images/generate",
            json={
                "prompt": "A beautiful fantasy landscape",
                "style": "whimsical"
            },
            headers=auth_headers
        )
        assert response.status_code == 201
        assert "url" in response.json()
        assert response.json()["url"] == "https://example.com/test.png"

    def test_enhance_prompt(self, client, auth_headers, mock_openai_client):
        """Test enhancing an image prompt."""
        response = client.post(
            "/api/images/enhance-prompt",
            json={
                "name": "Test Character",
                "traits": ["friendly", "brave"],
                "base_prompt": "A character standing"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "enhanced_prompt" in response.json()

    def test_unauthorized_image_access(self, client):
        """Test that unauthorized access to images is properly handled."""
        response = client.get("/api/images/1")
        assert response.status_code == 401
        assert "Unauthorized" in response.json()["message"]
        assert response.json()["error_code"] == "AUTH-001"

    def test_image_generation_with_style(self, client, auth_headers, mock_openai_client, mock_httpx_client):
        """Test generating an image with a specific style."""
        mock_openai_client.images.generate.return_value = {
            "data": [{"url": "https://example.com/styled.png"}]
        }

        response = client.post(
            "/api/images/generate",
            json={
                "prompt": "A magical forest",
                "style": "whimsical"
            },
            headers=auth_headers
        )
        assert response.status_code == 201
        assert "url" in response.json()
        assert response.json()["url"] == "https://example.com/styled.png"
        
        # Verify OpenAI client was called with style
        mock_openai_client.images.generate.assert_called_once()
        call_args = mock_openai_client.images.generate.call_args[1]
        assert "whimsical" in call_args.get("prompt", "").lower()


class TestEndToEndWorkflow:
    def test_character_to_story_workflow(self, client, auth_headers, mock_openai_client, mock_httpx_client):
        """Test the complete workflow from character creation to story generation."""
        # 1. Create a character
        character_response = client.post(
            "/api/characters/",
            json={
                "name": "Workflow Character",
                "traits": ["age: 10", "personality: friendly"],
                "image_prompt": "A friendly character"
            },
            headers=auth_headers
        )
        assert character_response.status_code in [200, 201]
        character_id = character_response.json()["id"]
        
        # 2. Generate a story
        generate_response = client.post(
            "/api/stories/generate",
            json={
                "title": "Workflow Story",
                "character_id": character_id,
                "age_group": "3-5",
                "story_tone": "whimsical",
                "moral_lesson": "kindness",
                "page_count": 3
            },
            headers=auth_headers
        )
        assert generate_response.status_code == 201
        assert "content" in generate_response.json()
        
        # 3. Generate images for each page
        for page in generate_response.json()["content"]["pages"]:
            image_response = client.post(
                "/api/images/generate",
                json={
                    "prompt": page["visual_description"],
                    "style": "whimsical"
                },
                headers=auth_headers
            )
            assert image_response.status_code == 201
            assert "url" in image_response.json() 