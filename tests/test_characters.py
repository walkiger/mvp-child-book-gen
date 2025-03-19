"""
Tests for the characters API functionality and error handling.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import HTTPException, status
import httpx
from datetime import datetime, UTC

from app.api.characters import create_character, get_user_characters, get_character
from app.database.models import Character, User, Image
from app.core.errors.characters import (
    CharacterError,
    CharacterNotFoundError,
    CharacterCreationError,
    CharacterValidationError
)
from app.core.errors.base import ErrorContext, ErrorSeverity, RetryConfig


@pytest.fixture
def error_context():
    """Create a test error context for character operations."""
    return ErrorContext(
        source="test.characters",
        severity=ErrorSeverity.ERROR,
        timestamp=datetime.now(UTC),
        error_id="test-char-id",
        additional_data={"operation": "test"}
    )


class TestCharactersAPI:
    @pytest.mark.asyncio
    async def test_create_character_success(self):
        """Test successful character creation."""
        # Mock database and objects
        mock_db = MagicMock()
        
        # Mock OpenAI client
        mock_client = MagicMock()
        
        # Mock image generation
        mock_images = ["https://example.com/image1.png", "https://example.com/image2.png"]
        
        # Mock user
        mock_user = User(id=1, email="user@example.com", username="testuser")
        
        # Mock character data
        character_data = MagicMock()
        character_data.name = "Test Character"
        character_data.traits = ["friendly", "creative", "smart"]
        
        # Mock HTTP client response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.content = b"fake_image_data"
        mock_response.headers = {"content-type": "image/png"}
        
        # Mock async HTTP client
        mock_http_client = AsyncMock()
        mock_http_client.__aenter__.return_value.get.return_value = mock_response
        
        with patch('app.api.characters.get_openai_client', return_value=mock_client), \
             patch('app.api.characters.generate_character_images', return_value=mock_images), \
             patch('httpx.AsyncClient', return_value=mock_http_client):
            # Call the function
            result = await create_character(character_data, mock_user, mock_db)
        
        # Verify the result
        assert result.name == "Test Character"
        assert result.user_id == 1
        assert hasattr(result, "generated_images")
        assert len(result.generated_images) == 2
        
        # Verify database operations
        mock_db.add.assert_called()
        assert mock_db.commit.call_count == 4
        assert mock_db.refresh.call_count >= 1

    @pytest.mark.asyncio
    async def test_create_character_validation_error(self):
        """Test character creation with invalid data."""
        mock_db = MagicMock()
        mock_user = User(id=1, email="user@example.com", username="testuser")
        
        # Mock character data with invalid traits
        character_data = MagicMock()
        character_data.name = ""  # Invalid empty name
        character_data.traits = []  # Invalid empty traits
        
        with pytest.raises(CharacterValidationError) as exc_info:
            await create_character(character_data, mock_user, mock_db)
        
        assert exc_info.value.error_code == "CHAR-VAL-001"
        assert "Invalid character data" in str(exc_info.value)
        assert exc_info.value.error_context.source == "api.characters"
        assert exc_info.value.error_context.severity == ErrorSeverity.ERROR
        assert "validation_errors" in exc_info.value.error_context.additional_data

    @pytest.mark.asyncio
    async def test_create_character_image_generation_error(self):
        """Test character creation with image generation failure."""
        mock_db = MagicMock()
        mock_user = User(id=1, email="user@example.com", username="testuser")
        mock_client = MagicMock()
        
        character_data = MagicMock()
        character_data.name = "Test Character"
        character_data.traits = ["friendly"]
        
        with patch('app.api.characters.get_openai_client', return_value=mock_client), \
             patch('app.api.characters.generate_character_images', side_effect=Exception("Image generation failed")):
            with pytest.raises(CharacterCreationError) as exc_info:
                await create_character(character_data, mock_user, mock_db)
        
        assert exc_info.value.error_code == "CHAR-IMG-001"
        assert "Failed to generate character images" in str(exc_info.value)
        assert exc_info.value.error_context.source == "api.characters.image_generation"
        assert exc_info.value.error_context.severity == ErrorSeverity.ERROR
        assert "character_name" in exc_info.value.error_context.additional_data
    
    @pytest.mark.asyncio
    async def test_get_user_characters(self):
        """Test retrieving all characters for a user."""
        mock_user = User(id=1, email="user@example.com", username="testuser")
        mock_db = MagicMock()
        
        mock_characters = [
            Character(id=1, name="Character 1", traits=["brave"], user_id=1),
            Character(id=2, name="Character 2", traits=["smart"], user_id=1)
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_characters
        
        result = await get_user_characters(mock_user, mock_db)
        
        assert len(result) == 2
        assert result[0]["name"] == "Character 1"
        assert result[1]["name"] == "Character 2"
    
    @pytest.mark.asyncio
    async def test_get_user_characters_empty(self):
        """Test retrieving characters when user has none."""
        mock_user = User(id=1, email="user@example.com", username="testuser")
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = await get_user_characters(mock_user, mock_db)
        
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_get_character_success(self):
        """Test retrieving a specific character by ID."""
        mock_character = Character(
            id=1, 
            name="Test Character", 
            traits=["brave", "smart"], 
            user_id=1,
            image_path="/path/to/image.png",
            generated_images=["https://example.com/image1.png"]
        )
        
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_character
        mock_user = User(id=1, email="user@example.com", username="testuser")
        
        result = await get_character(1, mock_user, mock_db)
        
        assert result["id"] == 1
        assert result["name"] == "Test Character"
        assert result["user_id"] == 1
        assert result["image_path"] == "/path/to/image.png"
        assert result["generated_images"] == ["https://example.com/image1.png"]
    
    @pytest.mark.asyncio
    async def test_get_character_not_found(self):
        """Test retrieving a non-existent character."""
        mock_db = MagicMock()
        mock_user = User(id=1, email="user@example.com", username="testuser")
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(CharacterNotFoundError) as exc_info:
            await get_character(999, mock_user, mock_db)

        assert exc_info.value.error_code == "CHAR-404"
        assert "Character not found: 999" in str(exc_info.value)
        assert exc_info.value.error_context.source == "api.characters"
        assert exc_info.value.error_context.severity == ErrorSeverity.ERROR
        assert exc_info.value.error_context.additional_data["character_id"] == 999
    
    @pytest.mark.asyncio
    async def test_get_character_unauthorized(self):
        """Test retrieving a character that belongs to another user."""
        mock_character = Character(
            id=1,
            name="Test Character",
            traits=["brave"],
            user_id=2  # Different user ID
        )
        
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_character
        mock_user = User(id=1, email="user@example.com", username="testuser")
        
        with pytest.raises(CharacterError) as exc_info:
            await get_character(1, mock_user, mock_db)
        
        assert exc_info.value.error_code == "CHAR-AUTH-001"
        assert "Unauthorized access to character" in str(exc_info.value)
        assert exc_info.value.error_context.source == "api.characters"
        assert exc_info.value.error_context.severity == ErrorSeverity.ERROR
        assert exc_info.value.error_context.additional_data["character_id"] == 1
        assert exc_info.value.error_context.additional_data["user_id"] == 1 