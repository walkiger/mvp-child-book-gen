"""
Tests for the stories API functionality.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi import HTTPException

from app.database.models import Story, Character, User
from app.schemas.story import StoryCreate


class TestStoriesAPI:
    @pytest.mark.asyncio
    async def test_create_story_success(self):
        """Test successful story creation."""
        # Mock database and objects
        mock_db = MagicMock()
        
        # Mock OpenAI client
        mock_client = AsyncMock()
        
        # Mock story generation
        mock_story_content = {
            "pages": [
                {"page_number": 1, "text": "Page 1 content", "visual_description": "A scene in a forest"},
                {"page_number": 2, "text": "Page 2 content", "visual_description": "A scene on a mountain"}
            ]
        }
        
        # Mock user and character
        mock_user = User(id=1, email="user@example.com", username="testuser")
        mock_character = Character(
            id=1, 
            name="Test Character", 
            traits=["friendly"], 
            user_id=1
        )
        
        # Mock database query to return the character
        mock_db.query.return_value.filter.return_value.first.return_value = mock_character
        
        # Mock story data with valid values
        story_data = StoryCreate(
            title="Test Story",
            age_group="6-9",  # Valid pattern: "^(1-2|3-6|6-9|10-12)$"
            character_id=1,
            page_count=2,
            moral_lesson="kindness",  # Valid pattern: "^(kindness|courage|friendship|honesty|perseverance)$"
            story_tone="adventurous",  # Valid pattern: "^(whimsical|educational|adventurous|calming)$"
            temperature=1.2
        )
        
        # Mock the generate_story function
        with pytest.MonkeyPatch.context() as mp:
            # Mock the OpenAI client
            mp.setattr("app.api.stories.get_openai_client", lambda: mock_client)
            
            # Mock the generate_story function
            mp.setattr("app.api.stories.generate_story", AsyncMock(return_value=mock_story_content))
            
            # Import the function after mocking
            from app.api.stories import create_story
            
            # Call the function
            result = await create_story(story_data, mock_user, mock_db)
        
        # Verify the result
        assert result.title == "Test Story"
        assert result.content == mock_story_content
        assert result.user_id == 1
        assert result.character_id == 1
        
        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_stories(self):
        """Test retrieving all stories for a user."""
        # Mock database and objects
        mock_db = MagicMock()
        
        # Mock user
        mock_user = User(id=1, email="user@example.com", username="testuser")
        
        # Mock stories
        mock_stories = [
            Story(
                id=1, 
                title="Story 1", 
                user_id=1, 
                character_id=1, 
                content={"pages": [{"text": "Page 1"}]},
                character=Character(name="Character 1")
            ),
            Story(
                id=2, 
                title="Story 2", 
                user_id=1, 
                character_id=2, 
                content={"pages": [{"text": "Page 1"}]},
                character=Character(name="Character 2")
            )
        ]
        
        # Mock database query to return the stories
        mock_db.query.return_value.filter.return_value.all.return_value = mock_stories
        
        # Import the function
        from app.api.stories import get_user_stories
        
        # Call the function
        result = await get_user_stories(mock_user, mock_db)
        
        # Verify the result
        assert len(result) == 2
        assert result[0]["title"] == "Story 1"
        assert result[1]["title"] == "Story 2"
        assert result[0]["character"]["name"] == "Character 1"
        assert result[1]["character"]["name"] == "Character 2"
    
    @pytest.mark.asyncio
    async def test_get_story_success(self):
        """Test retrieving a specific story by ID."""
        # Mock database and objects
        mock_db = MagicMock()
        
        # Mock user
        mock_user = User(id=1, email="user@example.com", username="testuser")
        
        # Mock story
        mock_story = Story(
            id=1, 
            title="Test Story", 
            user_id=1, 
            character_id=1, 
            content={"pages": [{"text": "Page content"}]}
        )
        
        # Mock database query to return the story
        mock_db.query.return_value.filter.return_value.first.return_value = mock_story
        
        # Import the function
        from app.api.stories import get_story
        
        # Call the function
        result = await get_story(1, mock_user, mock_db)
        
        # Verify the result
        assert result.id == 1
        assert result.title == "Test Story"
        assert result.user_id == 1
    
    @pytest.mark.asyncio
    async def test_get_story_not_found(self):
        """Test retrieving a non-existent story."""
        # Mock database and objects
        mock_db = MagicMock()
        
        # Mock user
        mock_user = User(id=1, email="user@example.com", username="testuser")
        
        # Mock database query to return None (story not found)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Import the function
        from app.api.stories import get_story
        
        # Call the function - should raise exception
        with pytest.raises(HTTPException) as excinfo:
            await get_story(999, mock_user, mock_db)
        
        # Verify the exception
        assert excinfo.value.status_code == 404
        assert "Story not found" in excinfo.value.detail 