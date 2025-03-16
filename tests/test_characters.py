"""
Tests for the characters API functionality.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import HTTPException, status

from app.api.characters import create_character, get_user_characters, get_character
from app.database.models import Character, User, Image


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
        
        with patch('app.api.characters.get_openai_client', return_value=mock_client), \
             patch('app.api.characters.generate_character_images', return_value=mock_images):
            # Call the function
            result = await create_character(character_data, mock_user, mock_db)
        
        # Verify the result
        assert result.name == "Test Character"
        assert result.user_id == 1
        assert hasattr(result, "generated_images")
        
        # Verify database operations
        mock_db.add.assert_called_once()
        # Commit is called twice - once after creating the character and once after updating with images
        assert mock_db.commit.call_count == 2
        assert mock_db.refresh.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_get_user_characters(self):
        """Test retrieving all characters for a user."""
        # Mock user
        mock_user = User(id=1, email="user@example.com", username="testuser")
        
        # Mock database
        mock_db = MagicMock()
        
        # Mock query result
        mock_characters = [
            Character(id=1, name="Character 1", traits=["brave"], user_id=1),
            Character(id=2, name="Character 2", traits=["smart"], user_id=1)
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_characters
        
        # Call the function
        result = await get_user_characters(mock_user, mock_db)
        
        # Verify the result
        assert len(result) == 2
        assert result[0]["name"] == "Character 1"
        assert result[1]["name"] == "Character 2"
    
    @pytest.mark.asyncio
    async def test_get_character_success(self):
        """Test retrieving a specific character by ID."""
        # Mock character
        mock_character = Character(
            id=1, 
            name="Test Character", 
            traits=["brave", "smart"], 
            user_id=1,
            image_path="/path/to/image.png",
            generated_images=["https://example.com/image1.png"]
        )
        
        # Mock database
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_character
        
        # Mock user
        mock_user = User(id=1, email="user@example.com", username="testuser")
        
        # Call the function
        result = await get_character(1, mock_user, mock_db)
        
        # Verify the result
        assert result["id"] == 1
        assert result["name"] == "Test Character"
        assert result["user_id"] == 1
    
    @pytest.mark.asyncio
    async def test_get_character_not_found(self):
        """Test retrieving a non-existent character."""
        # Mock database - no character found
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Mock user
        mock_user = User(id=1, email="user@example.com", username="testuser")
        
        # Call the function - should raise exception
        with pytest.raises(HTTPException) as excinfo:
            await get_character(999, mock_user, mock_db)
        
        # Verify the exception
        assert excinfo.value.status_code == 404
        assert "Character not found" in excinfo.value.detail 