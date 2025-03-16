"""
Tests for the database models.
"""
import pytest
import time
from sqlalchemy.exc import IntegrityError
from app.database.models import User, Character, Story, Image

# -----------------------------------------------------------------------------
# User Model Tests
# -----------------------------------------------------------------------------
class TestUserModel:
    def test_user_model_creation(self, test_db_session):
        """Test that a User model can be created and saved."""
        # Create a user
        user = User(
            username="testuser",
            email="test@example.com",
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
        saved_user = test_db_session.query(User).filter_by(username="testuser").first()
        assert saved_user is not None
        assert saved_user.email == "test@example.com"
        assert saved_user.first_name == "Test"
        assert saved_user.last_name == "User"

    def test_user_unique_constraints(self, test_db_session):
        """Test that username and email must be unique."""
        # Create a user
        user1 = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashedpassword",
            first_name="Test",
            last_name="User"
        )
        test_db_session.add(user1)
        test_db_session.commit()
        
        # Try to create another user with the same username
        user2 = User(
            username="testuser",
            email="different@example.com",
            password_hash="hashedpassword",
            first_name="Another",
            last_name="User"
        )
        test_db_session.add(user2)
        
        # Should raise IntegrityError for duplicate username
        with pytest.raises(IntegrityError):
            test_db_session.commit()
        
        # Rollback the failed transaction
        test_db_session.rollback()
        
        # Try to create another user with the same email
        user3 = User(
            username="differentuser",
            email="test@example.com",
            password_hash="hashedpassword",
            first_name="Another",
            last_name="User"
        )
        test_db_session.add(user3)
        
        # Should raise IntegrityError for duplicate email
        with pytest.raises(IntegrityError):
            test_db_session.commit()


# -----------------------------------------------------------------------------
# Character Model Tests
# -----------------------------------------------------------------------------
class TestCharacterModel:
    def test_character_model_creation(self, test_db_session):
        """Test that a Character model can be created and saved."""
        # Create a user first
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashedpassword",
            first_name="Test",
            last_name="User"
        )
        test_db_session.add(user)
        test_db_session.commit()
        
        # Create a character
        character = Character(
            user_id=user.id,
            name="Test Character",
            traits={"age": 10, "personality": "friendly"},
            image_prompt="A friendly character",
            image_path="/path/to/image.png",
            generated_images=["url1", "url2"]
        )
        
        # Add to session and commit
        test_db_session.add(character)
        test_db_session.commit()
        
        # Check that the character was saved with an ID
        assert character.id is not None
        
        # Query the character
        saved_character = test_db_session.query(Character).filter_by(name="Test Character").first()
        assert saved_character is not None
        assert saved_character.traits["age"] == 10
        assert saved_character.traits["personality"] == "friendly"
        assert saved_character.user_id == user.id

    @pytest.mark.parametrize("traits,should_pass", [
        ({"age": 10, "personality": "friendly"}, True),
        ({"age": "not_a_number", "personality": "friendly"}, True),  # Schema is flexible
        ({}, True),  # Empty traits is valid
        (None, True)  # Null traits is also valid in the model
    ])
    def test_character_traits_validation(self, test_db_session, traits, should_pass):
        """Test different character traits validation."""
        # Create a user first
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashedpassword",
            first_name="Test",
            last_name="User"
        )
        test_db_session.add(user)
        test_db_session.commit()
        
        # Create character with the provided traits
        character = Character(
            user_id=user.id,
            name="Test Character",
            traits=traits
        )
        
        test_db_session.add(character)
        
        # Try to commit the changes
        if should_pass:
            # Should commit successfully
            test_db_session.commit()
            assert character.id is not None
        else:
            # Should raise an exception
            with pytest.raises(Exception):
                test_db_session.commit()


# -----------------------------------------------------------------------------
# Story Model Tests
# -----------------------------------------------------------------------------
class TestStoryModel:
    def test_story_model_creation(self, test_db_session):
        """Test that a Story model can be created and saved."""
        # Create a user and character first
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashedpassword",
            first_name="Test",
            last_name="User"
        )
        test_db_session.add(user)
        test_db_session.commit()
        
        character = Character(
            user_id=user.id,
            name="Test Character",
            traits={"age": 10, "personality": "friendly"}
        )
        test_db_session.add(character)
        test_db_session.commit()
        
        # Create a story
        story = Story(
            user_id=user.id,
            character_id=character.id,
            title="Test Story",
            content={
                "pages": [
                    {"text": "Once upon a time...", "image_id": None},
                    {"text": "The end.", "image_id": None}
                ]
            },
            age_group="3-5",
            page_count=2,
            moral_lesson="kindness",
            story_tone="whimsical"
        )
        
        # Add to session and commit
        test_db_session.add(story)
        test_db_session.commit()
        
        # Check that the story was saved with an ID
        assert story.id is not None
        
        # Query the story
        saved_story = test_db_session.query(Story).filter_by(title="Test Story").first()
        assert saved_story is not None
        assert saved_story.age_group == "3-5"
        assert saved_story.moral_lesson == "kindness"
        assert saved_story.user_id == user.id
        assert saved_story.character_id == character.id
        assert len(saved_story.content["pages"]) == 2

    @pytest.mark.parametrize("age_group,should_pass", [
        ("3-5", True),
        ("6-8", True),
        ("9-12", True),
        ("invalid", False),
        (None, False)
    ])
    def test_story_age_group_constraint(self, test_db_session, age_group, should_pass):
        """Test that age_group must be one of the allowed values."""
        # Create a user and character first
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashedpassword",
            first_name="Test",
            last_name="User"
        )
        test_db_session.add(user)
        test_db_session.commit()
        
        character = Character(
            user_id=user.id,
            name="Test Character",
            traits={"age": 10, "personality": "friendly"}
        )
        test_db_session.add(character)
        test_db_session.commit()
        
        # Create a story with the specified age_group
        story = Story(
            user_id=user.id,
            character_id=character.id,
            title="Test Story",
            content={"pages": []},
            age_group=age_group,
            story_tone="whimsical"
        )
        
        # Add to session
        test_db_session.add(story)
        
        # Check validation
        if should_pass:
            test_db_session.commit()
            assert story.id is not None
        else:
            with pytest.raises(IntegrityError):
                test_db_session.commit()
            test_db_session.rollback()


# -----------------------------------------------------------------------------
# Image Model Tests
# -----------------------------------------------------------------------------
class TestImageModel:
    def test_image_model_creation(self, test_db_session):
        """Test that an Image model can be created and saved."""
        # Create user, character, and story
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashedpassword",
            first_name="Test",
            last_name="User"
        )
        test_db_session.add(user)
        test_db_session.commit()
        
        character = Character(
            user_id=user.id,
            name="Test Character",
            traits={"age": 10, "personality": "friendly"}
        )
        test_db_session.add(character)
        test_db_session.commit()
        
        story = Story(
            user_id=user.id,
            character_id=character.id,
            title="Test Story",
            content={"pages": []},
            age_group="3-5",
            story_tone="whimsical"
        )
        test_db_session.add(story)
        test_db_session.commit()
        
        # Create an image
        image = Image(
            story_id=story.id,
            character_id=character.id,
            image_data=b"test_image_data",
            image_format="png",
            dalle_version="dall-e-3"
        )
        
        # Add to session and commit
        test_db_session.add(image)
        test_db_session.commit()
        
        # Check that the image was saved with an ID
        assert image.id is not None
        
        # Query the image
        saved_image = test_db_session.query(Image).filter_by(story_id=story.id).first()
        assert saved_image is not None
        assert saved_image.image_format == "png"
        assert saved_image.dalle_version == "dall-e-3"

    @pytest.mark.parametrize("image_data,image_format,should_pass", [
        (b"binary_data", "png", True),
        (None, "png", False),  # Image data is required
        (b"binary_data", None, False),  # Image format is required
    ])
    def test_image_validation(self, test_db_session, image_data, image_format, should_pass):
        """Test validation of image data."""
        # Create required entities
        user = User(
            username="testuser",
            email="test@example.com",
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
        
        story = Story(
            user_id=user.id,
            character_id=character.id,
            title="Test Story",
            content={"pages": []},
            age_group="3-5"
        )
        test_db_session.add(story)
        test_db_session.commit()
        
        # Create image with test data
        image = Image(
            story_id=story.id,
            character_id=character.id,
            image_data=image_data,
            image_format=image_format,
            dalle_version="dall-e-3"
        )
        test_db_session.add(image)
        
        if should_pass:
            test_db_session.commit()
            assert image.id is not None
        else:
            with pytest.raises(Exception):
                test_db_session.commit()
            test_db_session.rollback()


# -----------------------------------------------------------------------------
# Relationship Tests
# -----------------------------------------------------------------------------
class TestRelationships:
    def test_model_relationships(self, test_db_session):
        """Test the relationships between models."""
        # Create a user
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashedpassword",
            first_name="Test",
            last_name="User"
        )
        test_db_session.add(user)
        test_db_session.commit()
        
        # Create a character
        character = Character(
            user_id=user.id,
            name="Test Character",
            traits={"age": 10, "personality": "friendly"}
        )
        test_db_session.add(character)
        test_db_session.commit()
        
        # Create a story
        story = Story(
            user_id=user.id,
            character_id=character.id,
            title="Test Story",
            content={"pages": []},
            age_group="3-5",
            story_tone="whimsical"
        )
        test_db_session.add(story)
        test_db_session.commit()
        
        # Create an image
        image = Image(
            story_id=story.id,
            character_id=character.id,
            image_data=b"test_image_data",
            image_format="png",
            dalle_version="dall-e-3"
        )
        test_db_session.add(image)
        test_db_session.commit()
        
        # Test user relationships
        assert user.characters[0].id == character.id
        assert user.stories[0].id == story.id
        
        # Test character relationships
        assert character.user.id == user.id
        assert character.stories[0].id == story.id
        assert character.images[0].id == image.id
        
        # Test story relationships
        assert story.user.id == user.id
        assert story.character.id == character.id
        assert story.images[0].id == image.id
        
        # Test image relationships
        assert image.story.id == story.id
        assert image.character.id == character.id


# -----------------------------------------------------------------------------
# Performance Tests
# -----------------------------------------------------------------------------
class TestModelPerformance:
    def test_bulk_character_creation_performance(self, test_db_session):
        """Test performance of bulk character creation."""
        # Create a user
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashedpassword",
            first_name="Test",
            last_name="User"
        )
        test_db_session.add(user)
        test_db_session.commit()
        
        start_time = time.time()
        
        # Create 50 characters in bulk
        characters = []
        for i in range(50):
            character = Character(
                user_id=user.id,
                name=f"Character {i}",
                traits={"personality": f"trait{i}"}
            )
            characters.append(character)
        
        test_db_session.add_all(characters)
        test_db_session.commit()
        
        duration = time.time() - start_time
        
        # Should be fast (under 0.5 seconds for in-memory SQLite)
        assert duration < 0.5, f"Bulk character creation took {duration:.2f} seconds"
        
        # Verify all characters were created
        character_count = test_db_session.query(Character).count()
        assert character_count == 50 