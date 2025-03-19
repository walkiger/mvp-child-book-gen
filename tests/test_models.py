"""
Tests for the database models and error handling.
"""
import pytest
import time
from datetime import datetime, timezone, UTC
import pytz
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

from app.database.models import User, Character, Story, Image
from app.core.errors.base import ErrorContext, ErrorSeverity, RetryConfig
from app.core.errors.database import (
    DatabaseError,
    DatabaseConnectionError,
    DatabaseValidationError,
    DatabaseIntegrityError,
    DatabasePerformanceError
)
from tests.conftest import generate_unique_email, generate_unique_username


@pytest.fixture
def error_context():
    """Create a test error context for database operations."""
    return ErrorContext(
        source="test.database",
        severity=ErrorSeverity.ERROR,
        timestamp=datetime.now(UTC),
        error_id="test-db-id",
        additional_data={"operation": "test"}
    )

# -----------------------------------------------------------------------------
# User Model Tests
# -----------------------------------------------------------------------------
class TestUserModel:
    def test_user_model_creation(self, test_db_session, error_context):
        """Test that a User model can be created and saved."""
        try:
            # Create a user
            user = User(
                username=generate_unique_username(),
                email=generate_unique_email(),
                password_hash="hashedpassword",
                first_name="Test",
                last_name="User"
            )
            
            # Add to session and commit
            test_db_session.add(user)
            test_db_session.commit()
            
            # Check that the user was saved with an ID
            assert user.id is not None
            
            # Query the user
            saved_user = test_db_session.query(User).filter_by(id=user.id).first()
            assert saved_user is not None
            assert saved_user.email == user.email
            assert saved_user.first_name == "Test"
            assert saved_user.last_name == "User"
        except Exception as e:
            error_context.additional_data.update({
                "user_email": user.email,
                "operation": "create_user"
            })
            raise DatabaseError("Failed to create user", error_context) from e

    def test_user_unique_constraints(self, test_db_session, error_context):
        """Test that username and email must be unique."""
        try:
            # Create a user
            email = generate_unique_email()
            username = generate_unique_username()
            user1 = User(
                username=username,
                email=email,
                password_hash="hashedpassword",
                first_name="Test",
                last_name="User"
            )
            test_db_session.add(user1)
            test_db_session.commit()
            
            # Try to create another user with the same username
            user2 = User(
                username=username,
                email=generate_unique_email(),
                password_hash="hashedpassword",
                first_name="Another",
                last_name="User"
            )
            test_db_session.add(user2)
            
            # Should raise DatabaseIntegrityError for duplicate username
            with pytest.raises(DatabaseIntegrityError) as exc_info:
                try:
                    test_db_session.commit()
                except IntegrityError as e:
                    error_context.additional_data.update({
                        "duplicate_field": "username",
                        "value": username
                    })
                    raise DatabaseIntegrityError("Duplicate username", error_context) from e
            
            assert exc_info.value.error_code == "DB-INT-001"
            assert "Duplicate username" in str(exc_info.value)
            assert exc_info.value.error_context.source == "test.database"
            assert exc_info.value.error_context.severity == ErrorSeverity.ERROR
            
            # Rollback the failed transaction
            test_db_session.rollback()
            
            # Try to create another user with the same email
            user3 = User(
                username=generate_unique_username(),
                email=email,
                password_hash="hashedpassword",
                first_name="Another",
                last_name="User"
            )
            test_db_session.add(user3)
            
            # Should raise DatabaseIntegrityError for duplicate email
            with pytest.raises(DatabaseIntegrityError) as exc_info:
                try:
                    test_db_session.commit()
                except IntegrityError as e:
                    error_context.additional_data.update({
                        "duplicate_field": "email",
                        "value": email
                    })
                    raise DatabaseIntegrityError("Duplicate email", error_context) from e
            
            assert exc_info.value.error_code == "DB-INT-001"
            assert "Duplicate email" in str(exc_info.value)
            assert exc_info.value.error_context.source == "test.database"
            assert exc_info.value.error_context.severity == ErrorSeverity.ERROR
        except Exception as e:
            error_context.additional_data.update({
                "operation": "test_unique_constraints"
            })
            raise DatabaseError("Failed to test unique constraints", error_context) from e

    def test_timezone_aware_timestamps(self, test_db_session, error_context):
        """Test that timestamps are timezone-aware and stored in UTC."""
        try:
            # Create a user
            user = User(
                username="timezone_test",
                email="timezone@example.com",
                password_hash="hashedpassword",
                first_name="Test",
                last_name="User"
            )
            test_db_session.add(user)
            test_db_session.commit()

            # Verify timestamps are timezone-aware and in UTC
            assert user.created_at.tzinfo is not None
            assert user.updated_at.tzinfo is not None
            
            # Test with different timezones
            tokyo_tz = pytz.timezone('Asia/Tokyo')
            ny_tz = pytz.timezone('America/New_York')
            
            # Convert timestamps to different timezones and verify they represent the same moment
            tokyo_time = user.created_at.astimezone(tokyo_tz)
            ny_time = user.created_at.astimezone(ny_tz)
            
            assert tokyo_time.timestamp() == ny_time.timestamp()
            assert user.created_at.timestamp() == tokyo_time.timestamp()
        except Exception as e:
            error_context.additional_data.update({
                "operation": "test_timezone_timestamps",
                "user_id": getattr(user, 'id', None)
            })
            raise DatabaseError("Failed to test timezone-aware timestamps", error_context) from e

    def test_auto_update_timestamp(self, test_db_session, error_context):
        """Test that updated_at is automatically updated."""
        try:
            # Create a user
            user = User(
                username="update_test",
                email="update@example.com",
                password_hash="hashedpassword",
                first_name="Test",
                last_name="User"
            )
            test_db_session.add(user)
            test_db_session.commit()
            
            original_updated_at = user.updated_at
            
            # Wait a second to ensure timestamp will be different
            time.sleep(1)
            
            # Update the user
            user.first_name = "Updated"
            test_db_session.commit()
            
            # Verify updated_at has changed and is timezone-aware
            assert user.updated_at > original_updated_at
            assert user.updated_at.tzinfo is not None
        except Exception as e:
            error_context.additional_data.update({
                "operation": "test_auto_update_timestamp",
                "user_id": getattr(user, 'id', None)
            })
            raise DatabaseError("Failed to test auto-update timestamp", error_context) from e


# -----------------------------------------------------------------------------
# Character Model Tests
# -----------------------------------------------------------------------------
class TestCharacterModel:
    def test_character_model_creation(self, test_db_session, error_context):
        """Test creating a character with valid data."""
        try:
            # Create a user first
            user = User(
                username=generate_unique_username(),
                email=generate_unique_email(),
                password_hash="hashedpassword",
                first_name="Test",
                last_name="User"
            )
            test_db_session.add(user)
            test_db_session.commit()

            # Create a character
            character = Character(
                name="Test Character",
                traits={"personality": "friendly", "appearance": "tall"},
                user_id=user.id
            )
            test_db_session.add(character)
            test_db_session.commit()

            # Verify character was created
            assert character.id is not None
            assert character.name == "Test Character"
            assert character.traits["personality"] == "friendly"
            assert character.user_id == user.id
        except Exception as e:
            error_context.additional_data.update({
                "operation": "create_character",
                "user_id": getattr(user, 'id', None),
                "character_name": "Test Character"
            })
            raise DatabaseError("Failed to create character", error_context) from e

    @pytest.mark.parametrize("traits,should_pass", [
        ({"personality": "friendly", "appearance": "tall"}, True),
        ({"personality": "shy"}, True),
        ({}, True),
        (None, True),
    ])
    def test_character_traits_validation(self, test_db_session, error_context, traits, should_pass):
        """Test validation of character traits."""
        try:
            # Create a user first
            user = User(
                username=generate_unique_username(),
                email=generate_unique_email(),
                password_hash="hashedpassword",
                first_name="Test",
                last_name="User"
            )
            test_db_session.add(user)
            test_db_session.commit()

            # Create a character
            character = Character(
                name="Test Character",
                traits=traits,
                user_id=user.id
            )
            test_db_session.add(character)
            
            if should_pass:
                test_db_session.commit()
                assert character.id is not None
            else:
                with pytest.raises(DatabaseValidationError) as exc_info:
                    try:
                        test_db_session.commit()
                    except IntegrityError as e:
                        error_context.additional_data.update({
                            "invalid_traits": traits,
                            "character_name": "Test Character"
                        })
                        raise DatabaseValidationError("Invalid character traits", error_context) from e
                
                assert exc_info.value.error_code == "DB-VAL-001"
                assert "Invalid character traits" in str(exc_info.value)
                assert exc_info.value.error_context.source == "test.database"
                assert exc_info.value.error_context.severity == ErrorSeverity.ERROR
        except Exception as e:
            error_context.additional_data.update({
                "operation": "test_character_traits",
                "traits": traits,
                "should_pass": should_pass
            })
            raise DatabaseError("Failed to test character traits validation", error_context) from e


# -----------------------------------------------------------------------------
# Story Model Tests
# -----------------------------------------------------------------------------
class TestStoryModel:
    def test_story_model_creation(self, test_db_session, error_context):
        """Test creating a story with valid data."""
        try:
            # Create a user first
            user = User(
                username=generate_unique_username(),
                email=generate_unique_email(),
                password_hash="hashedpassword",
                first_name="Test",
                last_name="User"
            )
            test_db_session.add(user)
            test_db_session.commit()

            # Create a character
            character = Character(
                name="Test Character",
                traits={"personality": "friendly"},
                user_id=user.id
            )
            test_db_session.add(character)
            test_db_session.commit()

            # Create a story
            story = Story(
                title="Test Story",
                age_group="6-8",
                moral_lesson="kindness",
                content={"pages": [{"text": "Once upon a time...", "image_prompt": "A happy scene"}]},
                character_id=character.id,
                user_id=user.id
            )
            test_db_session.add(story)
            test_db_session.commit()

            # Verify story was created
            assert story.id is not None
            assert story.title == "Test Story"
            assert story.age_group == "6-8"
            assert story.moral_lesson == "kindness"
            assert story.character_id == character.id
            assert story.user_id == user.id
            assert len(story.content["pages"]) == 1
        except Exception as e:
            error_context.additional_data.update({
                "operation": "create_story",
                "user_id": getattr(user, 'id', None),
                "character_id": getattr(character, 'id', None),
                "story_title": "Test Story"
            })
            raise DatabaseError("Failed to create story", error_context) from e

    @pytest.mark.parametrize("age_group,should_pass", [
        ("3-5", True),
        ("6-8", True),
        ("9-12", True),
        ("invalid", False),
        (None, False),
    ])
    def test_story_age_group_constraint(self, test_db_session, error_context, age_group, should_pass):
        """Test validation of story age group."""
        try:
            # Create a user and character first
            user = User(
                username=generate_unique_username(),
                email=generate_unique_email(),
                password_hash="hashedpassword"
            )
            test_db_session.add(user)
            test_db_session.commit()

            character = Character(
                name="Test Character",
                traits={"personality": "friendly"},
                user_id=user.id
            )
            test_db_session.add(character)
            test_db_session.commit()

            # Create a story
            story = Story(
                title="Test Story",
                age_group=age_group,
                moral_lesson="kindness",
                content={"pages": [{"text": "Test"}]},
                character_id=character.id,
                user_id=user.id
            )
            test_db_session.add(story)
            
            if should_pass:
                test_db_session.commit()
                assert story.id is not None
                assert story.age_group == age_group
            else:
                with pytest.raises(DatabaseValidationError) as exc_info:
                    try:
                        test_db_session.commit()
                    except IntegrityError as e:
                        error_context.additional_data.update({
                            "invalid_age_group": age_group,
                            "story_title": "Test Story"
                        })
                        raise DatabaseValidationError("Invalid story age group", error_context) from e
                
                assert exc_info.value.error_code == "DB-VAL-002"
                assert "Invalid story age group" in str(exc_info.value)
                assert exc_info.value.error_context.source == "test.database"
                assert exc_info.value.error_context.severity == ErrorSeverity.ERROR
        except Exception as e:
            error_context.additional_data.update({
                "operation": "test_age_group",
                "age_group": age_group,
                "should_pass": should_pass
            })
            raise DatabaseError("Failed to test story age group constraint", error_context) from e

    @pytest.mark.parametrize("story_tone,should_pass", [
        ("whimsical", True),
        ("educational", True),
        ("adventurous", True),
        ("calming", True),
        ("invalid_tone", False),
        (None, True)  # None should use the default value
    ])
    def test_story_tone_constraint(self, test_db_session, story_tone, should_pass):
        """Test that story_tone must be one of the allowed values."""
        # Create required entities
        user = User(
            username=generate_unique_username(),
            email=generate_unique_email(),
            password_hash="hashedpassword",
            first_name="Test",
            last_name="User"
        )
        test_db_session.add(user)
        test_db_session.commit()
        
        character = Character(
            user_id=user.id,
            name="Test Character",
            traits={"age": 10}
        )
        test_db_session.add(character)
        test_db_session.commit()
        
        # Create story with test tone
        story = Story(
            user_id=user.id,
            character_id=character.id,
            title="Test Story",
            content={"pages": []},
            age_group="3-5",
            story_tone=story_tone,
            moral_lesson="kindness"
        )
        test_db_session.add(story)
        
        if should_pass:
            test_db_session.commit()
            assert story.id is not None
            if story_tone is None:
                assert story.story_tone == "whimsical"  # Check default value
            else:
                assert story.story_tone == story_tone
        else:
            with pytest.raises(IntegrityError):
                test_db_session.commit()

    @pytest.mark.parametrize("moral_lesson,should_pass", [
        ("kindness", True),
        ("courage", True),
        ("friendship", True),
        ("honesty", True),
        ("perseverance", True),
        (None, True),
        ("invalid_lesson", False),
    ])
    def test_moral_lesson_constraint(self, test_db_session, moral_lesson, should_pass):
        """Test moral lesson constraint."""
        # Create a user first
        user = User(
            username=generate_unique_username(),
            email=generate_unique_email(),
            password_hash="hashedpassword",
            first_name="Test",
            last_name="User"
        )
        test_db_session.add(user)
        test_db_session.commit()

        # Create a character
        character = Character(
            name="Test Character",
            traits={"personality": "friendly"},
            user_id=user.id
        )
        test_db_session.add(character)
        test_db_session.commit()

        # Create a story
        story = Story(
            title="Test Story",
            age_group="6-8",
            moral_lesson=moral_lesson,
            content={"pages": [{"text": "Once upon a time...", "image_prompt": "A happy scene"}]},
            character_id=character.id,
            user_id=user.id
        )
        test_db_session.add(story)

        if should_pass:
            test_db_session.commit()
            assert story.id is not None
        else:
            with pytest.raises(IntegrityError):
                test_db_session.commit()

    def test_content_json_structure(self, test_db_session):
        """Test content JSON structure validation."""
        # Create a user first
        user = User(
            username=generate_unique_username(),
            email=generate_unique_email(),
            password_hash="hashedpassword",
            first_name="Test",
            last_name="User"
        )
        test_db_session.add(user)
        test_db_session.commit()

        # Create a character
        character = Character(
            name="Test Character",
            traits={"personality": "friendly"},
            user_id=user.id
        )
        test_db_session.add(character)
        test_db_session.commit()

        # Create a story with valid content structure
        story = Story(
            title="Test Story",
            age_group="6-8",
            moral_lesson="kindness",
            content={
                "pages": [
                    {
                        "text": "Once upon a time...",
                        "image_prompt": "A happy scene"
                    },
                    {
                        "text": "And they lived happily ever after.",
                        "image_prompt": "A joyful ending"
                    }
                ]
            },
            character_id=character.id,
            user_id=user.id
        )
        test_db_session.add(story)
        test_db_session.commit()

        # Verify story was created with correct content structure
        assert story.id is not None
        assert len(story.content["pages"]) == 2
        assert story.content["pages"][0]["text"] == "Once upon a time..."
        assert story.content["pages"][1]["image_prompt"] == "A joyful ending"


# -----------------------------------------------------------------------------
# Image Model Tests
# -----------------------------------------------------------------------------
class TestImageModel:
    def test_image_model_creation(self, test_db_session):
        """Test basic image model creation."""
        # Create required entities
        user = User(
            username=generate_unique_username(),
            email=generate_unique_email(),
            password_hash="hashedpassword",
            first_name="Test",
            last_name="User"
        )
        test_db_session.add(user)
        test_db_session.commit()

        character = Character(
            name="Test Character",
            traits={"personality": "friendly"},
            user_id=user.id
        )
        test_db_session.add(character)
        test_db_session.commit()

        story = Story(
            title="Test Story",
            age_group="6-8",
            moral_lesson="kindness",
            content={"pages": [{"text": "Once upon a time...", "image_prompt": "A happy scene"}]},
            character_id=character.id,
            user_id=user.id
        )
        test_db_session.add(story)
        test_db_session.commit()

        # Create an image
        image = Image(
            data=b"test_image_data",
            format="png",
            story_id=story.id,
            character_id=character.id,
            user_id=user.id
        )
        test_db_session.add(image)
        test_db_session.commit()

        # Verify the image was created
        assert image.id is not None
        assert image.data == b"test_image_data"
        assert image.format == "png"
        assert image.story_id == story.id
        assert image.character_id == character.id
        assert image.user_id == user.id

    @pytest.mark.parametrize("image_data,image_format,should_pass", [
        (b"binary_data", "png", True),
        (None, "png", False),  # Image data is required
        (b"binary_data", None, False),  # Image format is required
    ])
    def test_image_validation(self, test_db_session, image_data, image_format, should_pass):
        """Test validation of image data."""
        # Create required entities
        user = User(
            username=generate_unique_username(),
            email=generate_unique_email(),
            password_hash="hashedpassword",
            first_name="Test",
            last_name="User"
        )
        test_db_session.add(user)
        test_db_session.commit()

        character = Character(
            name="Test Character",
            traits={"personality": "friendly"},
            user_id=user.id
        )
        test_db_session.add(character)
        test_db_session.commit()

        story = Story(
            title="Test Story",
            age_group="6-8",
            moral_lesson="kindness",
            content={"pages": [{"text": "Once upon a time...", "image_prompt": "A happy scene"}]},
            character_id=character.id,
            user_id=user.id
        )
        test_db_session.add(story)
        test_db_session.commit()

        # Create an image
        image = Image(
            data=image_data,
            format=image_format,
            story_id=story.id,
            character_id=character.id,
            user_id=user.id
        )
        test_db_session.add(image)

        if should_pass:
            test_db_session.commit()
            assert image.id is not None
        else:
            with pytest.raises(Exception):
                test_db_session.commit()


# -----------------------------------------------------------------------------
# Relationship Tests
# -----------------------------------------------------------------------------
class TestRelationships:
    def test_model_relationships(self, test_db_session):
        """Test the relationships between models."""
        # Create a user
        user = User(
            username=generate_unique_username(),
            email=generate_unique_email(),
            password_hash="hashedpassword",
            first_name="Test",
            last_name="User"
        )
        test_db_session.add(user)
        test_db_session.commit()

        # Create a character
        character = Character(
            name="Test Character",
            traits={"personality": "friendly", "appearance": "tall"},
            user_id=user.id
        )
        test_db_session.add(character)
        test_db_session.commit()

        # Create a story
        story = Story(
            title="Test Story",
            age_group="6-8",
            moral_lesson="kindness",
            content={"pages": [{"text": "Once upon a time...", "image_prompt": "A happy scene"}]},
            character_id=character.id,
            user_id=user.id
        )
        test_db_session.add(story)
        test_db_session.commit()

        # Create an image
        image = Image(
            data=b"test_image_data",
            format="png",
            story_id=story.id,
            character_id=character.id,
            user_id=user.id
        )
        test_db_session.add(image)
        test_db_session.commit()

        # Test relationships
        assert user.characters[0] == character
        assert user.stories[0] == story
        assert user.images[0] == image
        assert character.user == user
        assert character.stories[0] == story
        assert character in user.characters
        assert story in user.stories
        assert image in user.images
        assert story in character.stories
        assert image in story.images
        assert story.character == character
        assert image.story == story
        assert image.user == user


# -----------------------------------------------------------------------------
# Performance Tests
# -----------------------------------------------------------------------------
class TestModelPerformance:
    def test_bulk_character_creation_performance(self, test_db_session, error_context):
        """Test performance of bulk character creation."""
        try:
            # Create a user first
            user = User(
                username=generate_unique_username(),
                email=generate_unique_email(),
                password_hash="hashedpassword"
            )
            test_db_session.add(user)
            test_db_session.commit()

            # Create multiple characters
            start_time = time.time()
            characters = []
            for i in range(100):
                character = Character(
                    name=f"Character {i}",
                    traits={"personality": "friendly"},
                    user_id=user.id
                )
                characters.append(character)
            
            test_db_session.add_all(characters)
            test_db_session.commit()
            end_time = time.time()

            # Verify performance
            creation_time = end_time - start_time
            if creation_time > 5.0:  # More than 5 seconds is too slow
                error_context.additional_data.update({
                    "operation": "bulk_character_creation",
                    "creation_time": creation_time,
                    "character_count": 100
                })
                raise DatabasePerformanceError(
                    "Bulk character creation performance degraded",
                    error_context
                )

            # Verify all characters were created
            assert len(characters) == 100
            for character in characters:
                assert character.id is not None
        except Exception as e:
            error_context.additional_data.update({
                "operation": "test_bulk_character_creation",
                "user_id": getattr(user, 'id', None)
            })
            raise DatabaseError("Failed to test bulk character creation", error_context) from e

    def test_bulk_story_creation_performance(self, test_db_session, error_context):
        """Test performance of bulk story creation."""
        try:
            # Create a user first
            user = User(
                username=generate_unique_username(),
                email=generate_unique_email(),
                password_hash="hashedpassword"
            )
            test_db_session.add(user)
            test_db_session.commit()

            # Create a character
            character = Character(
                name="Test Character",
                traits={"personality": "friendly"},
                user_id=user.id
            )
            test_db_session.add(character)
            test_db_session.commit()

            # Create multiple stories
            start_time = time.time()
            stories = []
            for i in range(50):
                story = Story(
                    title=f"Story {i}",
                    age_group="6-8",
                    moral_lesson="kindness",
                    content={"pages": [{"text": f"Story {i} content"}]},
                    character_id=character.id,
                    user_id=user.id
                )
                stories.append(story)
            
            test_db_session.add_all(stories)
            test_db_session.commit()
            end_time = time.time()

            # Verify performance
            creation_time = end_time - start_time
            if creation_time > 5.0:  # More than 5 seconds is too slow
                error_context.additional_data.update({
                    "operation": "bulk_story_creation",
                    "creation_time": creation_time,
                    "story_count": 50
                })
                raise DatabasePerformanceError(
                    "Bulk story creation performance degraded",
                    error_context
                )

            # Verify all stories were created
            assert len(stories) == 50
            for story in stories:
                assert story.id is not None
                assert story.title.startswith("Story ")
                assert story.age_group == "6-8"
                assert story.moral_lesson == "kindness"
                assert story.character_id == character.id
                assert story.user_id == user.id
        except Exception as e:
            error_context.additional_data.update({
                "operation": "test_bulk_story_creation",
                "user_id": getattr(user, 'id', None),
                "character_id": getattr(character, 'id', None)
            })
            raise DatabaseError("Failed to test bulk story creation", error_context) from e

    def test_bulk_image_creation_performance(self, test_db_session, error_context):
        """Test performance of bulk image creation."""
        try:
            # Create a user first
            user = User(
                username=generate_unique_username(),
                email=generate_unique_email(),
                password_hash="hashedpassword"
            )
            test_db_session.add(user)
            test_db_session.commit()

            # Create a character
            character = Character(
                name="Test Character",
                traits={"personality": "friendly"},
                user_id=user.id
            )
            test_db_session.add(character)
            test_db_session.commit()

            # Create a story
            story = Story(
                title="Test Story",
                age_group="6-8",
                moral_lesson="kindness",
                content={"pages": [{"text": "Test content"}]},
                character_id=character.id,
                user_id=user.id
            )
            test_db_session.add(story)
            test_db_session.commit()

            # Create multiple images
            start_time = time.time()
            images = []
            for i in range(20):  # Create 20 images
                image = Image(
                    data=b"test_image_data",
                    format="png",
                    story_id=story.id,
                    page_number=i + 1
                )
                images.append(image)
            
            test_db_session.add_all(images)
            test_db_session.commit()
            end_time = time.time()

            # Verify performance
            creation_time = end_time - start_time
            if creation_time > 3.0:  # More than 3 seconds is too slow
                error_context.additional_data.update({
                    "operation": "bulk_image_creation",
                    "creation_time": creation_time,
                    "image_count": 20
                })
                raise DatabasePerformanceError(
                    "Bulk image creation performance degraded",
                    error_context
                )

            # Verify all images were created
            assert len(images) == 20
            for image in images:
                assert image.id is not None
                assert image.story_id == story.id
                assert image.format == "png"
                assert image.data == b"test_image_data"
        except Exception as e:
            error_context.additional_data.update({
                "operation": "test_bulk_image_creation",
                "user_id": getattr(user, 'id', None),
                "story_id": getattr(story, 'id', None)
            })
            raise DatabaseError("Failed to test bulk image creation", error_context) from e

    def test_query_performance(self, test_db_session, error_context):
        """Test performance of complex queries."""
        try:
            # Create test data
            user = User(
                username=generate_unique_username(),
                email=generate_unique_email(),
                password_hash="hashedpassword"
            )
            test_db_session.add(user)
            test_db_session.commit()

            # Create multiple characters
            characters = []
            for i in range(10):
                character = Character(
                    name=f"Character {i}",
                    traits={"personality": "friendly"},
                    user_id=user.id
                )
                characters.append(character)
            test_db_session.add_all(characters)
            test_db_session.commit()

            # Create multiple stories for each character
            stories = []
            for character in characters:
                for i in range(5):  # 5 stories per character
                    story = Story(
                        title=f"Story {i} for {character.name}",
                        age_group="6-8",
                        moral_lesson="kindness",
                        content={"pages": [{"text": "Test content"}]},
                        character_id=character.id,
                        user_id=user.id
                    )
                    stories.append(story)
            test_db_session.add_all(stories)
            test_db_session.commit()

            # Test complex query performance
            start_time = time.time()
            
            # Complex query 1: Get all stories with their characters
            query1 = test_db_session.query(Story).join(Character).filter(
                Story.user_id == user.id,
                Story.age_group == "6-8"
            ).all()
            
            # Complex query 2: Get character with most stories
            query2 = test_db_session.query(
                Character,
                func.count(Story.id).label('story_count')
            ).join(Story).group_by(Character.id).order_by(
                func.count(Story.id).desc()
            ).first()
            
            end_time = time.time()

            # Verify performance
            query_time = end_time - start_time
            if query_time > 2.0:  # More than 2 seconds is too slow
                error_context.additional_data.update({
                    "operation": "complex_queries",
                    "query_time": query_time,
                    "story_count": len(stories),
                    "character_count": len(characters)
                })
                raise DatabasePerformanceError(
                    "Query performance degraded",
                    error_context
                )

            # Verify query results
            assert len(query1) == 50  # 10 characters * 5 stories each
            assert query2[1] == 5  # Each character has 5 stories
        except Exception as e:
            error_context.additional_data.update({
                "operation": "test_query_performance",
                "user_id": getattr(user, 'id', None)
            })
            raise DatabaseError("Failed to test query performance", error_context) from e

    def test_data_migration(self, test_db_session, error_context):
        """Test performance of data migration operations."""
        try:
            # Create initial test data
            user = User(
                username=generate_unique_username(),
                email=generate_unique_email(),
                password_hash="hashedpassword"
            )
            test_db_session.add(user)
            test_db_session.commit()

            # Create characters with old schema
            characters = []
            for i in range(10):
                character = Character(
                    name=f"Character {i}",
                    traits={"old_field": "value"},
                    user_id=user.id
                )
                characters.append(character)
            test_db_session.add_all(characters)
            test_db_session.commit()

            # Simulate data migration
            start_time = time.time()
            
            # Update character traits to new schema
            for character in characters:
                old_traits = character.traits
                character.traits = {
                    "personality": old_traits.get("old_field", "unknown"),
                    "appearance": "migrated",
                    "background": "migrated"
                }
            
            test_db_session.commit()
            end_time = time.time()

            # Verify performance
            migration_time = end_time - start_time
            if migration_time > 3.0:  # More than 3 seconds is too slow
                error_context.additional_data.update({
                    "operation": "data_migration",
                    "migration_time": migration_time,
                    "character_count": len(characters)
                })
                raise DatabasePerformanceError(
                    "Data migration performance degraded",
                    error_context
                )

            # Verify migration results
            for character in characters:
                assert "personality" in character.traits
                assert "appearance" in character.traits
                assert "background" in character.traits
                assert character.traits["appearance"] == "migrated"
                assert "old_field" not in character.traits
        except Exception as e:
            error_context.additional_data.update({
                "operation": "test_data_migration",
                "user_id": getattr(user, 'id', None)
            })
            raise DatabaseError("Failed to test data migration", error_context) from e 