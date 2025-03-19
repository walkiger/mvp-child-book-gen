"""
Tests for the stories API functionality and error handling.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi import HTTPException
from datetime import datetime, UTC

from app.database.models import Story, Character, User
from app.schemas.story import StoryCreate
from app.core.errors.stories import (
    StoryError,
    StoryNotFoundError,
    StoryCreationError,
    StoryValidationError,
    StoryGenerationError
)
from app.core.errors.base import ErrorContext, ErrorSeverity, RetryConfig


@pytest.fixture
def error_context():
    """Create a test error context for story operations."""
    return ErrorContext(
        source="test.stories",
        severity=ErrorSeverity.ERROR,
        timestamp=datetime.now(UTC),
        error_id="test-story-id",
        additional_data={"operation": "test"}
    )


class TestStoriesAPI:
    @pytest.mark.asyncio
    async def test_create_story_success(self):
        """Test successful story creation."""
        mock_db = MagicMock()
        mock_client = AsyncMock()
        
        mock_story_content = {
            "pages": [
                {"page_number": 1, "text": "Page 1 content", "visual_description": "A scene in a forest"},
                {"page_number": 2, "text": "Page 2 content", "visual_description": "A scene on a mountain"}
            ]
        }
        
        mock_user = User(id=1, email="user@example.com", username="testuser")
        mock_character = Character(
            id=1, 
            name="Test Character", 
            traits=["friendly"], 
            user_id=1,
            image_prompt="A friendly character",
            images=[]
        )
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_character
        
        story_data = StoryCreate(
            title="Test Story",
            age_group="6-8",
            character_id=1,
            page_count=2,
            moral_lesson="kindness",
            story_tone="adventurous",
            temperature=1.2
        )
        
        mock_story = Story(
            id=1,
            title="Test Story",
            user_id=1,
            character_id=1,
            content=mock_story_content,
            age_group="6-8",
            story_tone="adventurous",
            moral_lesson="kindness",
            status="completed",
            page_count=2,
            created_at="2024-03-20T12:00:00Z"
        )
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh = MagicMock(return_value=None)
        
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr("app.api.stories.get_openai_client", lambda: mock_client)
            mp.setattr("app.api.stories.generate_story", AsyncMock(return_value=mock_story_content))
            mp.setattr("app.api.stories.Story", MagicMock(return_value=mock_story))
            
            from app.api.stories import create_story
            result = await create_story(story_data, mock_user, mock_db)
        
        assert isinstance(result, dict)
        assert result["id"] == 1
        assert result["user_id"] == 1
        assert result["title"] == "Test Story"
        assert result["content"] == mock_story_content
        assert result["age_group"] == "6-8"
        assert result["story_tone"] == "adventurous"
        assert result["moral_lesson"] == "kindness"
        assert result["page_count"] == 2
        assert result["status"] == "completed"
        assert result["character_id"] == 1
        assert result["created_at"] == "2024-03-20T12:00:00Z"
        
        assert result["character"]["id"] == 1
        assert result["character"]["name"] == "Test Character"
        assert result["character"]["traits"] == ["friendly"]
        assert result["character"]["image_prompt"] == "A friendly character"
        assert result["character"]["images"] == []

    @pytest.mark.asyncio
    async def test_create_story_validation_error(self):
        """Test story creation with invalid data."""
        mock_db = MagicMock()
        mock_user = User(id=1, email="user@example.com", username="testuser")
        
        story_data = StoryCreate(
            title="",  # Invalid empty title
            age_group="invalid",  # Invalid age group
            character_id=1,
            page_count=0,  # Invalid page count
            moral_lesson="invalid",  # Invalid moral lesson
            story_tone="invalid",  # Invalid story tone
            temperature=2.0  # Invalid temperature
        )
        
        from app.api.stories import create_story
        with pytest.raises(StoryValidationError) as exc_info:
            await create_story(story_data, mock_user, mock_db)
        
        assert exc_info.value.error_code == "STORY-VAL-001"
        assert "Invalid story data" in str(exc_info.value)
        assert exc_info.value.error_context.source == "api.stories"
        assert exc_info.value.error_context.severity == ErrorSeverity.ERROR
        assert "validation_errors" in exc_info.value.error_context.additional_data

    @pytest.mark.asyncio
    async def test_create_story_generation_error(self):
        """Test story creation with generation failure."""
        mock_db = MagicMock()
        mock_user = User(id=1, email="user@example.com", username="testuser")
        mock_client = AsyncMock()
        
        story_data = StoryCreate(
            title="Test Story",
            age_group="6-8",
            character_id=1,
            page_count=2,
            moral_lesson="kindness",
            story_tone="adventurous",
            temperature=1.0
        )
        
        mock_character = Character(id=1, name="Test Character", traits=["friendly"], user_id=1)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_character
        
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr("app.api.stories.get_openai_client", lambda: mock_client)
            mp.setattr("app.api.stories.generate_story", AsyncMock(side_effect=Exception("Story generation failed")))
            
            from app.api.stories import create_story
            with pytest.raises(StoryGenerationError) as exc_info:
                await create_story(story_data, mock_user, mock_db)
        
        assert exc_info.value.error_code == "STORY-GEN-001"
        assert "Failed to generate story" in str(exc_info.value)
        assert exc_info.value.error_context.source == "api.stories.generation"
        assert exc_info.value.error_context.severity == ErrorSeverity.ERROR
        assert "story_title" in exc_info.value.error_context.additional_data
    
    @pytest.mark.asyncio
    async def test_get_user_stories(self):
        """Test retrieving all stories for a user."""
        mock_db = MagicMock()
        mock_user = User(id=1, email="user@example.com", username="testuser")
        
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
        
        mock_db.query.return_value.filter.return_value.all.return_value = mock_stories
        
        from app.api.stories import get_user_stories
        result = await get_user_stories(mock_user, mock_db)
        
        assert len(result) == 2
        assert result[0]["title"] == "Story 1"
        assert result[1]["title"] == "Story 2"
        assert result[0]["character"]["name"] == "Character 1"
        assert result[1]["character"]["name"] == "Character 2"
    
    @pytest.mark.asyncio
    async def test_get_user_stories_empty(self):
        """Test retrieving stories when user has none."""
        mock_db = MagicMock()
        mock_user = User(id=1, email="user@example.com", username="testuser")
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        from app.api.stories import get_user_stories
        result = await get_user_stories(mock_user, mock_db)
        
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_get_story_success(self):
        """Test retrieving a specific story by ID."""
        mock_db = MagicMock()
        mock_user = User(id=1, email="user@example.com", username="testuser")
        
        mock_story = Story(
            id=1, 
            title="Test Story", 
            user_id=1, 
            character_id=1, 
            content={"pages": [{"text": "Page content"}]},
            character=Character(name="Test Character")
        )
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_story
        
        from app.api.stories import get_story
        result = await get_story(1, mock_user, mock_db)
        
        assert result.id == 1
        assert result.title == "Test Story"
        assert result.user_id == 1
        assert result.character.name == "Test Character"
    
    @pytest.mark.asyncio
    async def test_get_story_not_found(self):
        """Test retrieving a non-existent story."""
        mock_db = MagicMock()
        mock_user = User(id=1, email="user@example.com", username="testuser")
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        from app.api.stories import get_story
        with pytest.raises(StoryNotFoundError) as exc_info:
            await get_story(999, mock_user, mock_db)
        
        assert exc_info.value.error_code == "STORY-404"
        assert "Story not found: 999" in str(exc_info.value)
        assert exc_info.value.error_context.source == "api.stories"
        assert exc_info.value.error_context.severity == ErrorSeverity.ERROR
        assert exc_info.value.error_context.additional_data["story_id"] == 999
    
    @pytest.mark.asyncio
    async def test_get_story_unauthorized(self):
        """Test retrieving a story that belongs to another user."""
        mock_db = MagicMock()
        mock_user = User(id=1, email="user@example.com", username="testuser")
        
        mock_story = Story(
            id=1,
            title="Test Story",
            user_id=2,  # Different user ID
            character_id=1,
            content={"pages": [{"text": "Page content"}]}
        )
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_story
        
        from app.api.stories import get_story
        with pytest.raises(StoryError) as exc_info:
            await get_story(1, mock_user, mock_db)
        
        assert exc_info.value.error_code == "STORY-AUTH-001"
        assert "Unauthorized access to story" in str(exc_info.value)
        assert exc_info.value.error_context.source == "api.stories"
        assert exc_info.value.error_context.severity == ErrorSeverity.ERROR
        assert exc_info.value.error_context.additional_data["story_id"] == 1
        assert exc_info.value.error_context.additional_data["user_id"] == 1 