# app/api/stories.py

"""
Story management API endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.auth import get_current_user
from app.database.models import User, Story, Character
from app.database.session import get_db
from app.schemas.story import StoryCreate, StoryResponse, StoryUpdate
from app.core.story_generation import generate_story
from app.core.image_generation import generate_story_page_images
from app.core.openai_client import get_openai_client
from app.core.story_errors import (
    StoryNotFoundError,
    StoryCreationError,
    StoryUpdateError,
    StoryGenerationError,
    StoryValidationError,
    StoryDeletionError
)
from app.core.character_errors import CharacterNotFoundError
from app.core.error_handling import setup_logger

# Set up logger
logger = setup_logger("stories", "logs/stories.log")

router = APIRouter(tags=["stories"])


@router.post("/", response_model=StoryResponse)
async def create_story(
    story: StoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new story with the specified parameters.
    """
    try:
        # Verify character exists and belongs to user
        character = db.query(Character).filter(
            Character.id == story.character_id,
            Character.user_id == current_user.id
        ).first()
        
        if not character:
            raise CharacterNotFoundError(story.character_id)
        
        logger.info(f"Generating story for character {character.name}")
        
        # Generate story using GPT-4
        openai_client = get_openai_client()
        try:
            story_content = await generate_story(
                openai_client,
                character.name,
                character.traits,
                story.title,
                story.age_group,
                story.page_count,
                story.story_tone,
                story.moral_lesson
            )
        except Exception as e:
            logger.error(f"Error generating story content: {str(e)}")
            raise StoryGenerationError(
                message="Failed to generate story content",
                details=str(e)
            )
        
        # Create story in database
        db_story = Story(
            user_id=current_user.id,
            title=story.title,
            content=story_content,
            age_group=story.age_group,
            page_count=story.page_count,
            character_id=story.character_id,
            moral_lesson=story.moral_lesson,
            story_tone=story.story_tone
        )
        
        try:
            db.add(db_story)
            db.commit()
            db.refresh(db_story)
            logger.info(f"Story created successfully with ID: {db_story.id}")
            return db_story
        except Exception as e:
            logger.error(f"Error saving story to database: {str(e)}")
            db.rollback()
            raise StoryCreationError(
                message="Failed to save story to database",
                details=str(e)
            )
            
    except (CharacterNotFoundError, StoryGenerationError, StoryCreationError) as e:
        # Re-raise known errors
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating story: {str(e)}")
        raise StoryCreationError(
            message="Failed to create story",
            details=str(e)
        )


@router.post("/{story_id}/generate-images")
async def generate_page_images(
    story_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
            raise StoryNotFoundError(story_id)
        
        logger.info(f"Generating images for story {story_id}")
        
        # Generate images for each page
        openai_client = get_openai_client()
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
            logger.error(f"Error generating story images: {str(e)}")
            raise StoryGenerationError(
                message="Failed to generate story images",
                details=str(e)
            )
            
    except (StoryNotFoundError, StoryGenerationError) as e:
        # Re-raise known errors
        raise
    except Exception as e:
        logger.error(f"Unexpected error generating story images: {str(e)}")
        raise StoryGenerationError(
            message="Failed to generate story images",
            details=str(e)
        )


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
    story = db.query(Story).filter(
        Story.id == story_id,
        Story.user_id == current_user.id
    ).first()
    
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    if page_number < 1 or page_number > story.page_count:
        raise HTTPException(status_code=400, detail="Invalid page number")
    
    # Save the selected image
    # Note: In a real implementation, you would save the actual image file
    image_path = f"stories/{story_id}/page_{page_number}_image_{image_index}.png"
    
    # Update the story content to include the selected image
    story.content[page_number - 1]["image_path"] = image_path
    db.commit()
    
    return {"message": "Image selected successfully"}


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
    story = db.query(Story).filter(
        Story.id == story_id,
        Story.user_id == current_user.id
    ).first()
    
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    if page_number < 1 or page_number > story.page_count:
        raise HTTPException(status_code=400, detail="Invalid page number")
    
    # Update the page text
    story.content[page_number - 1]["text"] = new_text
    db.commit()
    
    return {"message": "Page text updated successfully"}


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
        logger.error(f"Error retrieving user stories: {str(e)}")
        raise StoryNotFoundError(
            story_id=0,  # Generic ID for list operation
            details=f"Failed to retrieve stories: {str(e)}"
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
            raise StoryNotFoundError(story_id)
        
        return story
        
    except StoryNotFoundError:
        # Re-raise known errors
        raise
    except Exception as e:
        logger.error(f"Error retrieving story {story_id}: {str(e)}")
        raise StoryNotFoundError(
            story_id=story_id,
            details=str(e)
        )


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
            raise StoryNotFoundError(story_id)
        
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
            logger.error(f"Error updating story in database: {str(e)}")
            db.rollback()
            raise StoryUpdateError(
                story_id=story_id,
                details=str(e)
            )
            
    except (StoryNotFoundError, StoryUpdateError) as e:
        # Re-raise known errors
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating story {story_id}: {str(e)}")
        raise StoryUpdateError(
            story_id=story_id,
            details=str(e)
        )


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
            raise StoryNotFoundError(story_id)
        
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
            logger.error(f"Error deleting story from database: {str(e)}")
            db.rollback()
            raise StoryDeletionError(
                story_id=story_id,
                details=str(e)
            )
            
    except (StoryNotFoundError, StoryDeletionError) as e:
        # Re-raise known errors
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting story {story_id}: {str(e)}")
        raise StoryDeletionError(
            story_id=story_id,
            details=str(e)
        )