# app/api/stories.py

"""
Story-related API endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
import logging
from uuid import uuid4
from datetime import datetime, UTC

from app.database.models import Story, User, Character
from app.database.session import get_db
from app.schemas.story import (
    StoryCreate,
    StoryResponse,
    StoryUpdate
)
from app.core.auth import get_current_user
from app.core.openai_client import get_openai_client
from app.core.errors.story import (
    StoryError,
    StoryNotFoundError,
    StoryCreationError,
    StoryGenerationError,
    StoryValidationError,
    StoryUpdateError,
    StoryDeletionError
)
from app.core.errors.character import CharacterNotFoundError
from app.core.errors.base import ErrorContext, ErrorSeverity
from app.core.story_generation import generate_story, enhance_story_content
from app.core.image_generation import generate_story_page_images
from app.core.logging import setup_logger
from app.core.rate_limiter import rate_limiter

# Set up logger
logger = setup_logger("stories", "logs/stories.log")

# Initialize story progress tracking
story_progress = {}

router = APIRouter(tags=["stories"])


@router.post("/", response_model=StoryResponse, status_code=201)
async def create_story(
    story: StoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    openai_client = Depends(get_openai_client)
):
    """
    Create a new story with generated content and images.
    """
    try:
        # Validate character ownership
        character = db.query(Character).filter(
            Character.id == story.character_id,
            Character.user_id == current_user.id
        ).first()
        
        if not character:
            raise CharacterNotFoundError(
                character_id=story.character_id,
                context=ErrorContext(
                    source="stories.create_story",
                    severity=ErrorSeverity.WARNING,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "user_id": current_user.id,
                        "character_id": story.character_id
                    }
                )
            )
        
        # Create story in database first
        db_story = Story(
            user_id=current_user.id,
            character_id=story.character_id,
            title=story.title if story.title else "",
            age_group=story.age_group,
            story_tone=story.story_tone,
            moral_lesson=story.moral_lesson,
            status="generating"
        )
        
        try:
            db.add(db_story)
            db.commit()
            db.refresh(db_story)
        except Exception as e:
            db.rollback()
            raise StoryCreationError(
                message="Failed to create story in database",
                context=ErrorContext(
                    source="stories.create_story",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "user_id": current_user.id,
                        "character_id": story.character_id,
                        "error": str(e)
                    }
                )
            )
        
        # Initialize progress tracking
        story_progress[db_story.id] = {
            "progress": 0,
            "status": "generating",
            "message": "Starting story generation..."
        }
        
        # Generate story content
        story_content = await generate_story(
            client=openai_client,
            character_name=character.name,
            character_traits=character.traits,
            title=story.title,
            age_group=story.age_group,
            page_count=story.page_count,
            story_tone=story.story_tone,
            moral_lesson=story.moral_lesson
        )
        
        # Update story in database
        db_story.content = story_content
        db_story.page_count = story.page_count
        db_story.status = "completed"
        
        try:
            db.commit()
            db.refresh(db_story)
            logger.info(f"Story created successfully with ID: {db_story.id}")
            
            # Convert to response format
            response = {
                "id": db_story.id,
                "user_id": db_story.user_id,
                "title": db_story.title,
                "content": db_story.content,
                "age_group": db_story.age_group,
                "story_tone": db_story.story_tone,
                "moral_lesson": db_story.moral_lesson,
                "page_count": db_story.page_count,
                "status": db_story.status,
                "created_at": db_story.created_at,
                "character_id": db_story.character_id,
                "character": {
                    "id": character.id,
                    "name": character.name,
                    "traits": character.traits,
                    "image_prompt": character.image_prompt,
                    "images": [
                        {
                            "id": img.id,
                            "url": f"/api/images/{img.id}",
                            "format": img.format
                        }
                        for img in (character.images or [])
                    ]
                }
            }
            return response
            
        except Exception as e:
            db.rollback()
            raise StoryUpdateError(
                message="Failed to update story with generated content",
                context=ErrorContext(
                    source="stories.create_story",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "story_id": db_story.id,
                        "user_id": current_user.id,
                        "error": str(e)
                    }
                )
            )
            
    except StoryGenerationError as e:
        # Update story status to failed
        if 'db_story' in locals():
            db_story.status = "failed"
            db.commit()
        raise StoryGenerationError(
            message=str(e),
            context=ErrorContext(
                source="stories.create_story",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={
                    "story_id": getattr(db_story, 'id', None),
                    "user_id": current_user.id,
                    "error": str(e)
                }
            )
        )
    except Exception as e:
        # Handle any other unexpected errors
        if 'db_story' in locals():
            db_story.status = "failed"
            db.commit()
        raise StoryError(
            message="Unexpected error during story creation",
            context=ErrorContext(
                source="stories.create_story",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={
                    "story_id": getattr(db_story, 'id', None),
                    "user_id": current_user.id,
                    "error": str(e)
                }
            )
        )


@router.post("/{story_id}/generate-images")
async def generate_page_images(
    story_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    openai_client = Depends(get_openai_client)
):
    """
    Generate images for all pages of a story.
    """
    try:
        story = db.query(Story).filter(
            Story.id == story_id,
            Story.user_id == current_user.id
        ).first()
        
        if not story:
            raise StoryNotFoundError(
                story_id=story_id,
                context=ErrorContext(
                    source="stories.generate_page_images",
                    severity=ErrorSeverity.WARNING,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={"user_id": current_user.id}
                )
            )
        
        logger.info(f"Generating images for story {story_id}")
        
        try:
            images = await generate_story_page_images(
                openai_client,
                story.content,
                story.character.name,
                story.character.traits
            )
            logger.info(f"Successfully generated {len(images)} images for story {story_id}")
            return {"generated_images": images}
        except Exception as e:
            raise StoryGenerationError(
                message="Failed to generate story images",
                context=ErrorContext(
                    source="stories.generate_page_images",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "story_id": story_id,
                        "user_id": current_user.id,
                        "error": str(e)
                    }
                )
            )
            
    except Exception as e:
        if not isinstance(e, (StoryNotFoundError, StoryGenerationError)):
            raise StoryError(
                message="Unexpected error generating story images",
                context=ErrorContext(
                    source="stories.generate_page_images",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "story_id": story_id,
                        "user_id": current_user.id,
                        "error": str(e)
                    }
                )
            )
        raise


@router.post("/{story_id}/select-page-image")
async def select_page_image(
    story_id: int,
    page_number: int,
    image_index: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Select and save an image for a specific page.
    """
    try:
        story = db.query(Story).filter(
            Story.id == story_id,
            Story.user_id == current_user.id
        ).first()
        
        if not story:
            raise StoryNotFoundError(
                story_id=story_id,
                context=ErrorContext(
                    source="stories.select_page_image",
                    severity=ErrorSeverity.WARNING,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={"user_id": current_user.id}
                )
            )
        
        if page_number < 1 or page_number > story.page_count:
            raise StoryValidationError(
                message="Invalid page number",
                context=ErrorContext(
                    source="stories.select_page_image",
                    severity=ErrorSeverity.WARNING,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "story_id": story_id,
                        "page_number": page_number,
                        "page_count": story.page_count
                    }
                )
            )
        
        # Save the selected image
        image_path = f"stories/{story_id}/page_{page_number}_image_{image_index}.png"
        
        try:
            # Update the story content to include the selected image
            story.content[page_number - 1]["image_path"] = image_path
            db.commit()
            
            return {"message": "Image selected successfully"}
        except Exception as e:
            db.rollback()
            raise StoryUpdateError(
                message="Failed to save selected image",
                context=ErrorContext(
                    source="stories.select_page_image",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "story_id": story_id,
                        "page_number": page_number,
                        "image_index": image_index,
                        "error": str(e)
                    }
                )
            )
    except Exception as e:
        if not isinstance(e, (StoryNotFoundError, StoryValidationError, StoryUpdateError)):
            raise StoryError(
                message="Unexpected error selecting page image",
                context=ErrorContext(
                    source="stories.select_page_image",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "story_id": story_id,
                        "page_number": page_number,
                        "image_index": image_index,
                        "error": str(e)
                    }
                )
            )
        raise


@router.put("/{story_id}/page/{page_number}")
async def update_page_text(
    story_id: int,
    page_number: int,
    new_text: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update the text of a specific page.
    """
    try:
        story = db.query(Story).filter(
            Story.id == story_id,
            Story.user_id == current_user.id
        ).first()
        
        if not story:
            raise StoryNotFoundError(
                story_id=story_id,
                context=ErrorContext(
                    source="stories.update_page_text",
                    severity=ErrorSeverity.WARNING,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={"user_id": current_user.id}
                )
            )
        
        if page_number < 1 or page_number > story.page_count:
            raise StoryValidationError(
                message="Invalid page number",
                context=ErrorContext(
                    source="stories.update_page_text",
                    severity=ErrorSeverity.WARNING,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "story_id": story_id,
                        "page_number": page_number,
                        "page_count": story.page_count
                    }
                )
            )
        
        try:
            # Update the page text
            story.content[page_number - 1]["text"] = new_text
            db.commit()
            
            return {"message": "Page text updated successfully"}
        except Exception as e:
            db.rollback()
            raise StoryUpdateError(
                message="Failed to update page text",
                context=ErrorContext(
                    source="stories.update_page_text",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "story_id": story_id,
                        "page_number": page_number,
                        "error": str(e)
                    }
                )
            )
    except Exception as e:
        if not isinstance(e, (StoryNotFoundError, StoryValidationError, StoryUpdateError)):
            raise StoryError(
                message="Unexpected error updating page text",
                context=ErrorContext(
                    source="stories.update_page_text",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "story_id": story_id,
                        "page_number": page_number,
                        "error": str(e)
                    }
                )
            )
        raise


@router.get("/", response_model=List[StoryResponse])
async def get_user_stories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all stories for the current user.
    """
    try:
        stories = db.query(Story).filter(Story.user_id == current_user.id).all()
        
        # Convert stories to response format
        response_stories = []
        for story in stories:
            story_dict = {
                "id": story.id,
                "user_id": story.user_id,
                "title": story.title,
                "content": story.content,
                "age_group": story.age_group,
                "page_count": story.page_count,
                "character_id": story.character_id,
                "story_tone": story.story_tone,
                "moral_lesson": story.moral_lesson,
                "created_at": story.created_at.isoformat() if story.created_at else None,
                "character": {
                    "name": story.character.name
                }
            }
            response_stories.append(story_dict)
        
        return response_stories
        
    except Exception as e:
        raise StoryError(
            message="Failed to retrieve user stories",
            context=ErrorContext(
                source="stories.get_user_stories",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={
                    "user_id": current_user.id,
                    "error": str(e)
                }
            )
        )


@router.get("/{story_id}", response_model=StoryResponse)
async def get_story(
    story_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific story by ID.
    """
    try:
        story = db.query(Story).filter(
            Story.id == story_id,
            Story.user_id == current_user.id
        ).first()
        
        if not story:
            raise StoryNotFoundError(
                story_id=story_id,
                context=ErrorContext(
                    source="stories.get_story",
                    severity=ErrorSeverity.WARNING,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={"user_id": current_user.id}
                )
            )
        
        return story
        
    except Exception as e:
        if not isinstance(e, StoryNotFoundError):
            raise StoryError(
                message="Failed to retrieve story",
                context=ErrorContext(
                    source="stories.get_story",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "story_id": story_id,
                        "user_id": current_user.id,
                        "error": str(e)
                    }
                )
            )
        raise


@router.put("/{story_id}", response_model=StoryResponse)
async def update_story(
    story_id: int,
    story_data: StoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a story by ID.
    """
    try:
        # Find the story
        story = db.query(Story).filter(
            Story.id == story_id,
            Story.user_id == current_user.id
        ).first()
        
        if not story:
            raise StoryNotFoundError(
                story_id=story_id,
                context=ErrorContext(
                    source="stories.update_story",
                    severity=ErrorSeverity.WARNING,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={"user_id": current_user.id}
                )
            )
        
        # Update story fields
        update_data = story_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(story, field, value)
            
        try:
            db.commit()
            db.refresh(story)
            logger.info(f"Story {story_id} updated successfully")
            return story
        except Exception as e:
            db.rollback()
            raise StoryUpdateError(
                message="Failed to update story in database",
                context=ErrorContext(
                    source="stories.update_story",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "story_id": story_id,
                        "user_id": current_user.id,
                        "error": str(e)
                    }
                )
            )
            
    except Exception as e:
        if not isinstance(e, (StoryNotFoundError, StoryUpdateError)):
            raise StoryError(
                message="Unexpected error updating story",
                context=ErrorContext(
                    source="stories.update_story",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "story_id": story_id,
                        "user_id": current_user.id,
                        "error": str(e)
                    }
                )
            )
        raise


@router.delete("/{story_id}")
async def delete_story(
    story_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a story by ID.
    
    Returns:
        dict: {"success": boolean, "message": str} - Result of the delete operation
    """
    try:
        # Find the story
        story = db.query(Story).filter(
            Story.id == story_id,
            Story.user_id == current_user.id
        ).first()
        
        if not story:
            raise StoryNotFoundError(
                story_id=story_id,
                context=ErrorContext(
                    source="stories.delete_story",
                    severity=ErrorSeverity.WARNING,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={"user_id": current_user.id}
                )
            )
        
        try:
            # Delete the story
            db.delete(story)
            db.commit()
            logger.info(f"Story {story_id} deleted successfully")
            
            return {
                "success": True,
                "message": f"Story '{story.title}' deleted successfully"
            }
        except Exception as e:
            db.rollback()
            raise StoryDeletionError(
                message="Failed to delete story from database",
                context=ErrorContext(
                    source="stories.delete_story",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "story_id": story_id,
                        "user_id": current_user.id,
                        "error": str(e)
                    }
                )
            )
            
    except Exception as e:
        if not isinstance(e, (StoryNotFoundError, StoryDeletionError)):
            raise StoryError(
                message="Unexpected error deleting story",
                context=ErrorContext(
                    source="stories.delete_story",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "story_id": story_id,
                        "user_id": current_user.id,
                        "error": str(e)
                    }
                )
            )
        raise


@router.post("/generate", response_model=StoryResponse, status_code=201)
async def generate_story_endpoint(
    request: Request,
    story: StoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    openai_client = Depends(get_openai_client)
):
    """
    Generate a new story with AI.
    """
    try:
        # Check OpenAI rate limits before making the API call
        rate_limiter.check_rate_limit(request, "openai_chat")

        # Verify character exists and belongs to user
        character = db.query(Character).filter(
            Character.id == story.character_id,
            Character.user_id == current_user.id
        ).first()

        if not character:
            raise CharacterNotFoundError(
                character_id=story.character_id,
                context=ErrorContext(
                    source="stories.generate_story_endpoint",
                    severity=ErrorSeverity.WARNING,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={"user_id": current_user.id}
                )
            )

        logger.info(f"Generating story for character {character.name}")

        try:
            story_content = await generate_story(
                client=openai_client,
                character_name=character.name,
                character_traits=character.traits,
                title=story.title,
                age_group=story.age_group,
                page_count=story.page_count,
                story_tone=story.story_tone,
                moral_lesson=story.moral_lesson
            )
        except Exception as e:
            raise StoryGenerationError(
                message="Failed to generate story content",
                context=ErrorContext(
                    source="stories.generate_story_endpoint",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "character_id": character.id,
                        "user_id": current_user.id,
                        "error": str(e)
                    }
                )
            )

        # Create story in database
        db_story = Story(
            user_id=current_user.id,
            character_id=character.id,
            title=story.title,
            content=story_content,
            age_group=story.age_group,
            story_tone=story.story_tone,
            moral_lesson=story.moral_lesson,
            page_count=story.page_count,
            status="completed",
            generation_cost=0.02  # Estimate cost
        )

        db.add(db_story)
        db.commit()
        db.refresh(db_story)

        return db_story

    except Exception as e:
        if not isinstance(e, (CharacterNotFoundError, StoryGenerationError)):
            raise StoryError(
                message="Unexpected error generating story",
                context=ErrorContext(
                    source="stories.generate_story_endpoint",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "user_id": current_user.id,
                        "error": str(e)
                    }
                )
            )
        raise


@router.post("/{story_id}/regenerate", response_model=StoryResponse)
async def regenerate_story(
    story_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    openai_client = Depends(get_openai_client)
):
    """
    Regenerate a story's content and images.
    """
    try:
        # Get the story
        story = db.query(Story).filter(
            Story.id == story_id,
            Story.user_id == current_user.id
        ).first()
        
        if not story:
            raise StoryNotFoundError(
                story_id=story_id,
                context=ErrorContext(
                    source="stories.regenerate_story",
                    severity=ErrorSeverity.WARNING,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={"user_id": current_user.id}
                )
            )
        
        # Get the character
        character = db.query(Character).filter(
            Character.id == story.character_id
        ).first()
        
        if not character:
            raise CharacterNotFoundError(
                character_id=story.character_id,
                context=ErrorContext(
                    source="stories.regenerate_story",
                    severity=ErrorSeverity.WARNING,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "story_id": story_id,
                        "user_id": current_user.id
                    }
                )
            )
        
        # Update story status
        story.status = "regenerating"
        db.commit()
        
        # Initialize progress tracking
        story_progress[story.id] = {
            "progress": 0,
            "status": "regenerating",
            "message": "Starting story regeneration..."
        }
        
        try:
            # Generate new story content
            story_content = await generate_story(
                client=openai_client,
                character_name=character.name,
                character_traits=character.traits,
                title=story.title,
                age_group=story.age_group,
                page_count=story.page_count,
                story_tone=story.story_tone,
                moral_lesson=story.moral_lesson
            )
            
            # Update story content
            story.content = story_content
            db.commit()
            
            # Generate new images
            images = await generate_story_page_images(
                openai_client,
                story_content,
                character.name,
                character.traits
            )
            
            # Update story images
            story.images = images
            db.commit()
            
            return story
            
        except Exception as e:
            db.rollback()
            story.status = "failed"
            db.commit()
            raise StoryGenerationError(
                message="Failed to regenerate story",
                context=ErrorContext(
                    source="stories.regenerate_story",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "story_id": story_id,
                        "character_id": character.id,
                        "user_id": current_user.id,
                        "error": str(e)
                    }
                )
            )
            
    except Exception as e:
        if not isinstance(e, (StoryNotFoundError, CharacterNotFoundError, StoryGenerationError)):
            raise StoryError(
                message="Unexpected error regenerating story",
                context=ErrorContext(
                    source="stories.regenerate_story",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "story_id": story_id,
                        "user_id": current_user.id,
                        "error": str(e)
                    }
                )
            )
        raise


@router.post("/{story_id}/enhance", response_model=StoryResponse)
async def enhance_story(
    story_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    openai_client = Depends(get_openai_client)
):
    """
    Enhance a story's content by making it more engaging and descriptive.
    """
    try:
        # Get the story
        story = db.query(Story).filter(
            Story.id == story_id,
            Story.user_id == current_user.id
        ).first()
        
        if not story:
            raise StoryNotFoundError(
                story_id=story_id,
                context=ErrorContext(
                    source="stories.enhance_story",
                    severity=ErrorSeverity.WARNING,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={"user_id": current_user.id}
                )
            )
        
        # Update story status
        story.status = "enhancing"
        db.commit()
        
        # Initialize progress tracking
        story_progress[story.id] = {
            "progress": 0,
            "status": "enhancing",
            "message": "Starting story enhancement..."
        }
        
        try:
            # Enhance story content
            enhanced_content = await enhance_story_content(
                openai_client,
                story
            )
            
            # Update story content
            story.content = enhanced_content
            story.status = "completed"
            db.commit()
            
            return story
            
        except Exception as e:
            db.rollback()
            story.status = "failed"
            db.commit()
            raise StoryGenerationError(
                message="Failed to enhance story",
                context=ErrorContext(
                    source="stories.enhance_story",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "story_id": story_id,
                        "user_id": current_user.id,
                        "error": str(e)
                    }
                )
            )
            
    except Exception as e:
        if not isinstance(e, (StoryNotFoundError, StoryGenerationError)):
            raise StoryError(
                message="Unexpected error enhancing story",
                context=ErrorContext(
                    source="stories.enhance_story",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "story_id": story_id,
                        "user_id": current_user.id,
                        "error": str(e)
                    }
                )
            )
        raise