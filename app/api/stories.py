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
    # Verify character exists and belongs to user
    character = db.query(Character).filter(
        Character.id == story.character_id,
        Character.user_id == current_user.id
    ).first()
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Generate story using GPT-4
    openai_client = get_openai_client()
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
    
    db.add(db_story)
    db.commit()
    db.refresh(db_story)
    
    return db_story


@router.post("/{story_id}/generate-images")
async def generate_page_images(
    story_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate images for all pages of a story.
    """
    story = db.query(Story).filter(
        Story.id == story_id,
        Story.user_id == current_user.id
    ).first()
    
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    # Generate images for each page
    openai_client = get_openai_client()
    images = await generate_story_page_images(
        openai_client,
        story.content,
        story.character.name,
        story.character.traits
    )
    
    return {"generated_images": images}


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


@router.get("/{story_id}", response_model=StoryResponse)
async def get_story(
    story_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific story by ID.
    """
    story = db.query(Story).filter(
        Story.id == story_id,
        Story.user_id == current_user.id
    ).first()
    
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    return story