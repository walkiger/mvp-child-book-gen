"""
Character management API endpoints.
"""

from typing import List, Dict, Any, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, BackgroundTasks, Query, Request
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.orm import Session
from app.core.auth import get_current_user
from app.database.models import User, Character, Image
from app.database.session import get_db
from app.schemas.character import CharacterCreate, CharacterResponse, CharacterUpdate, CharacterImageGenerationProgress, PromptEnhanceRequest, CharacterRefineRequest
from app.core.image_generation import generate_character_images, enhance_image_prompt
from app.core.openai_client import get_openai_client
from app.core.rate_limiter import rate_limiter
from app.core.errors.character import (
    CharacterError,
    CharacterNotFoundError,
    CharacterCreationError,
    CharacterUpdateError,
    CharacterImageError,
    CharacterValidationError,
    CharacterDeletionError
)
from app.core.errors.base import ErrorContext, ErrorSeverity
from app.core.logging import setup_logger
import asyncio
import json
import httpx
import io
import os
from datetime import datetime, UTC
from uuid import uuid4
import re

# Set up logger
logger = setup_logger("characters", "logs/characters.log")

router = APIRouter(tags=["characters"])

# Add a dictionary to store generation progress
generation_progress: Dict[int, Dict[str, Any]] = {}

@router.get("/{character_id}/generation-status")
async def get_generation_status(
    character_id: int,
    current_user: User = Depends(get_current_user)
) -> EventSourceResponse:
    """
    Server-sent events endpoint for real-time image generation updates.
    """
    if character_id not in generation_progress:
        raise CharacterNotFoundError(
            character_id=character_id,
            context=ErrorContext(
                source="characters.get_generation_status",
                severity=ErrorSeverity.WARNING,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={
                    "user_id": current_user.id,
                    "error": "No generation progress found"
                }
            )
        )
        
    async def event_generator():
        while True:
            if character_id in generation_progress:
                data = generation_progress[character_id]
                yield {
                    "event": "message",
                    "data": json.dumps({
                        "progress": data["progress"],
                        "images": data["images"],
                        "complete": data["complete"]
                    })
                }
                if data["complete"]:
                    del generation_progress[character_id]
                    break
            await asyncio.sleep(1)
    
    return EventSourceResponse(event_generator())

@router.post("/", response_model=CharacterResponse)
async def create_character(
    request: Request,
    character: CharacterCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    openai_client = Depends(get_openai_client)
):
    """
    Create a new character with generated images.
    """
    logger.info("Starting character creation...")
    
    try:
        # Check OpenAI rate limits for prompt enhancement
        rate_limiter.check_rate_limit(request, "openai_chat")
        
        # Get DALL-E version from request or use default
        dalle_version = getattr(character, 'dalle_version', 'dall-e-3')
        
        # Create character in database first
        db_character = Character(
            user_id=current_user.id,
            name=character.name,
            traits=character.traits,
            image_prompt=f"Create a child-friendly character illustration for {character.name} with traits: {', '.join(character.traits)}"
        )
        
        logger.info("Adding character to database...")
        db.add(db_character)
        db.commit()
        db.refresh(db_character)
        logger.info(f"Character created with ID: {db_character.id}")
        
        # Initialize progress tracking
        generation_progress[db_character.id] = {
            "progress": 0,
            "images": [],
            "complete": False
        }
        
        # Define progress callback
        def progress_callback(progress: int, image_url: str = None):
            if image_url:
                if "images" not in generation_progress[db_character.id]:
                    generation_progress[db_character.id]["images"] = []
                generation_progress[db_character.id]["images"].append(image_url)
            generation_progress[db_character.id]["progress"] = progress
            logger.info(f"Progress update: {progress}/2, Image URL: {image_url if image_url else 'None'}")
        
        logger.info("Starting image generation...")
        
        # Check OpenAI rate limits for image generation
        rate_limiter.check_rate_limit(request, "openai_image")
        
        try:
            # Generate character images
            image_urls = await generate_character_images(
                openai_client,
                character.name,
                character.traits,
                dalle_version,
                progress_callback
            )
        except Exception as e:
            logger.error(f"Error generating images: {str(e)}")
            raise CharacterImageError(
                message="Failed to generate character images",
                details=str(e)
            )
            
        # Store generated images
        stored_image_paths = []
        for i, url in enumerate(image_urls):
            try:
                # Create image record
                db_image = Image(
                    user_id=current_user.id,
                    character_id=db_character.id,
                    url=url,
                    format="png",
                    width=1024,
                    height=1024,
                    prompt=db_character.image_prompt,
                    model=dalle_version
                )
                
                db.add(db_image)
                db.commit()
                db.refresh(db_image)
                
                # Store reference to our database image
                stored_image_paths.append(f"/api/images/{db_image.id}")
            except Exception as e:
                logger.error(f"Error processing image {i}: {str(e)}")
                raise CharacterImageError(
                    message=f"Error processing image {i}",
                    details=str(e)
                )
        
        # Update progress
        generation_progress[db_character.id]["complete"] = True
        generation_progress[db_character.id]["images"] = stored_image_paths
        
        # Update the character with generated images
        logger.info("Updating character with generated images...")
        db_character.generated_images = stored_image_paths
        
        # Set the first image as the default image path
        if stored_image_paths:
            db_character.image_path = stored_image_paths[0]
            
        db.commit()
        db.refresh(db_character)
        
        return db_character
        
    except Exception as e:
        logger.error(f"Error during character creation: {str(e)}")
        if db_character and db_character.id in generation_progress:
            del generation_progress[db_character.id]
        raise CharacterCreationError(
            message="Failed to create character",
            context=ErrorContext(
                source="characters.create_character",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={
                    "user_id": current_user.id,
                    "character_name": character.name,
                    "error": str(e)
                }
            )
        )

@router.post("/{character_id}/select-image")
async def select_character_image(
    character_id: int,
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Select an image for a character from generated images.
    
    Parameters:
    - image_index: The index of the image to select
    """
    try:
        character = db.query(Character).filter(
            Character.id == character_id,
            Character.user_id == current_user.id
        ).first()
        
        if not character:
            raise CharacterNotFoundError(
                character_id=character_id,
                context=ErrorContext(
                    source="characters.select_character_image",
                    severity=ErrorSeverity.WARNING,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={"user_id": current_user.id}
                )
            )
        
        if not character.generated_images:
            raise CharacterImageError(
                message="No generated images available",
                context=ErrorContext(
                    source="characters.select_character_image",
                    severity=ErrorSeverity.WARNING,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "character_id": character_id,
                        "user_id": current_user.id
                    }
                )
            )
        
        # Get the image index from the request
        image_index = data.get("image_index")
        if image_index is None:
            raise CharacterValidationError(
                message="Image index is required",
                context=ErrorContext(
                    source="characters.select_character_image",
                    severity=ErrorSeverity.WARNING,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "character_id": character_id,
                        "user_id": current_user.id,
                        "error": "Missing image_index field"
                    }
                )
            )
        
        try:
            image_index = int(image_index)
        except ValueError:
            raise CharacterValidationError(
                message="Image index must be a number",
                context=ErrorContext(
                    source="characters.select_character_image",
                    severity=ErrorSeverity.WARNING,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "character_id": character_id,
                        "user_id": current_user.id,
                        "provided_value": image_index
                    }
                )
            )
        
        # Check if the index is valid
        if image_index < 0 or image_index >= len(character.generated_images):
            raise CharacterValidationError(
                message="Invalid image index",
                context=ErrorContext(
                    source="characters.select_character_image",
                    severity=ErrorSeverity.WARNING,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "character_id": character_id,
                        "user_id": current_user.id,
                        "provided_index": image_index,
                        "valid_range": f"0-{len(character.generated_images) - 1}"
                    }
                )
            )
        
        # Get the image reference
        image_reference = character.generated_images[image_index]
        
        # Handle both legacy URL and new database ID reference formats
        if image_reference.startswith("/api/images/"):
            # New format
            character.image_path = image_reference
        else:
            # Legacy format or direct URL
            character.image_path = image_reference
        
        db.commit()
        
        return {
            "success": True,
            "message": "Image selected successfully",
            "image_path": character.image_path
        }
        
    except (CharacterNotFoundError, CharacterImageError, CharacterValidationError) as e:
        # Re-raise known errors
        raise
    except Exception as e:
        logger.error(f"Error selecting character image: {str(e)}")
        raise CharacterUpdateError(
            character_id=character_id,
            details=str(e)
        )

@router.post("/{character_id}/regenerate", response_model=CharacterResponse)
async def regenerate_character_images(
    character_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    openai_client = Depends(get_openai_client)
):
    """
    Regenerate images for an existing character.
    """
    try:
        # Get the character
        character = db.query(Character).filter(
            Character.id == character_id,
            Character.user_id == current_user.id
        ).first()
        
        if not character:
            raise CharacterNotFoundError(character_id)
        
        # Initialize progress tracking
        generation_progress[character.id] = {
            "progress": 0,
            "images": [],
            "complete": False
        }
        
        # Define progress callback
        def progress_callback(progress: int, image_url: str = None):
            if image_url:
                if "images" not in generation_progress[character.id]:
                    generation_progress[character.id]["images"] = []
                generation_progress[character.id]["images"].append(image_url)
            generation_progress[character.id]["progress"] = progress
            logger.info(f"Progress update: {progress}/2, Image URL: {image_url if image_url else 'None'}")
        
        # Generate new images
        raw_image_urls = await generate_character_images(
            openai_client,
            character.name,
            character.traits,
            progress_callback=progress_callback
        )
        
        # Update character in database
        character.generated_images = raw_image_urls
        db.commit()
        
        return {"generated_images": raw_image_urls}
        
    except CharacterNotFoundError:
        # Re-raise known errors
        raise
    except Exception as e:
        logger.error(f"Error regenerating character images: {str(e)}")
        raise CharacterImageError(
            message="Failed to regenerate character images",
            details=str(e)
        )

@router.get("/", response_model=List[CharacterResponse])
async def get_user_characters(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all characters for the current user.
    """
    try:
        characters = db.query(Character).filter(Character.user_id == current_user.id).all()
        
        # Convert characters to response format
        response_characters = []
        for character in characters:
            character_dict = {
                "id": character.id,
                "user_id": character.user_id,
                "name": character.name,
                "traits": character.traits or [],
                "image_path": character.image_path,
                "generated_images": getattr(character, 'generated_images', None)
            }
            response_characters.append(character_dict)
        
        return response_characters
        
    except Exception as e:
        logger.error(f"Error retrieving user characters: {str(e)}")
        raise CharacterNotFoundError(
            character_id=0,  # Generic ID for list operation
            details=f"Failed to retrieve characters: {str(e)}"
        )

@router.get("/{character_id}", response_model=CharacterResponse)
async def get_character(
    character_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a character by ID.
    """
    character = db.query(Character).filter(
        Character.id == character_id,
        Character.user_id == current_user.id
    ).first()
    
    if not character:
        raise CharacterNotFoundError(
            character_id=character_id,
            context=ErrorContext(
                source="characters.get_character",
                severity=ErrorSeverity.WARNING,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"user_id": current_user.id}
            )
        )
    
    return character

@router.put("/{character_id}", response_model=CharacterResponse)
async def update_character(
    character_id: int,
    character_update: CharacterUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a character by ID.
    """
    try:
        character = db.query(Character).filter(
            Character.id == character_id,
            Character.user_id == current_user.id
        ).first()
        
        if not character:
            raise CharacterNotFoundError(
                character_id=character_id,
                context=ErrorContext(
                    source="characters.update_character",
                    severity=ErrorSeverity.WARNING,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={"user_id": current_user.id}
                )
            )
        
        # Update character fields
        update_data = character_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(character, field, value)
            
        try:
            db.commit()
            db.refresh(character)
            return character
        except Exception as e:
            db.rollback()
            raise CharacterUpdateError(
                message="Failed to update character",
                context=ErrorContext(
                    source="characters.update_character",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "character_id": character_id,
                        "user_id": current_user.id,
                        "error": str(e)
                    }
                )
            )
            
    except Exception as e:
        if not isinstance(e, (CharacterNotFoundError, CharacterUpdateError)):
            raise CharacterError(
                message="Unexpected error updating character",
                context=ErrorContext(
                    source="characters.update_character",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "character_id": character_id,
                        "user_id": current_user.id,
                        "error": str(e)
                    }
                )
            )
        raise

@router.post("/{character_id}/generate-image")
async def generate_single_image(
    character_id: int,
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a single image for a character with specific parameters.
    
    Parameters:
    - index: The index of the image (0-3)
    - dalle_version: The DALL-E version to use ('dall-e-2' or 'dall-e-3')
    - prompt: Optional custom prompt to use
    """
    try:
        # Apply rate limiting
        if not rate_limiter.check("image_generation", current_user.id):
            raise CharacterImageError(
                message="Rate limit exceeded for image generation",
                details="Please try again later"
            )
            
        character = db.query(Character).filter(
            Character.id == character_id,
            Character.user_id == current_user.id
        ).first()
        
        if not character:
            raise CharacterNotFoundError(character_id)
        
        # Get parameters
        index = data.get("index", 0)
        dalle_version = data.get("dalle_version", "dall-e-3")
        custom_prompt = data.get("prompt")
        
        # Check if this is a regeneration request
        is_regeneration = False
        if character.generated_images and len(character.generated_images) > index and character.generated_images[index]:
            is_regeneration = True
            
            # If it's a regeneration, check if we already have an image for this position
            existing_image_path = character.generated_images[index]
            if existing_image_path and existing_image_path.startswith("/api/images/"):
                image_id = int(existing_image_path.split("/")[-1])
                existing_image = db.query(Image).filter(Image.id == image_id).first()
                
                if existing_image and existing_image.regeneration_count >= 1:
                    raise CharacterImageError(
                        message="Maximum image regeneration limit reached",
                        details="Each image can only be regenerated once"
                    )
        
        # Use provided prompt or character's default prompt
        prompt = custom_prompt or character.image_prompt or f"Create a child-friendly character illustration for {character.name} with traits: {', '.join(character.traits)}"
        
        # Get OpenAI client
        openai_client = get_openai_client()
        
        # Generate single image
        response = await openai_client.images.generate(
            model=dalle_version,
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        
        image_url = response.data[0].url
        
        # Download the image
        async with httpx.AsyncClient() as client:
            img_response = await client.get(image_url)
            if img_response.status_code != 200:
                raise CharacterImageError(
                    message="Failed to download generated image",
                    details=f"Status code: {img_response.status_code}"
                )
                
            # Get image data and format
            image_data = img_response.content
            content_type = img_response.headers.get("content-type", "")
            image_format = content_type.split("/")[-1] if "/" in content_type else "png"
            
            # If this is a regeneration, update the existing image's regeneration count
            if is_regeneration and 'existing_image' in locals() and existing_image:
                existing_image.regeneration_count += 1
                existing_image.data = image_data
                existing_image.format = image_format
                existing_image.dalle_version = dalle_version
                existing_image.generation_cost += 0.02 if dalle_version == "dall-e-3" else 0.01
                existing_image.generated_at = datetime.now(UTC)
                db.commit()
                db.refresh(existing_image)
                
                # Use the same image path
                image_path = f"/api/images/{existing_image.id}"
            else:
                # Create new image record in database
                db_image = Image(
                    character_id=character_id,
                    user_id=current_user.id,
                    story_id=None,  # This is a character image, not a story image
                    data=image_data,
                    format=image_format,
                    dalle_version=dalle_version,
                    generation_cost=0.02 if dalle_version == "dall-e-3" else 0.01,  # Estimate cost
                    grid_position=index,
                    regeneration_count=0  # New image, no regenerations yet
                )
                db.add(db_image)
                db.commit()
                db.refresh(db_image)
                
                # Create reference to the image
                image_path = f"/api/images/{db_image.id}"
            
            # Update character's generated images list
            if not character.generated_images:
                character.generated_images = []
            
            # If index is out of range, append to the list
            current_images = character.generated_images
            if isinstance(current_images, list):
                while len(current_images) <= index:
                    current_images.append(None)
                current_images[index] = image_path
                character.generated_images = current_images
                
                # If no image path is set, use this image
                if not character.image_path:
                    character.image_path = image_path
                    
                db.commit()
            
            # Add prompt to response for hover functionality
            return {
                "success": True,
                "image_url": image_path,
                "index": index,
                "dalle_version": dalle_version,
                "prompt": prompt,
                "regeneration_count": existing_image.regeneration_count if is_regeneration and 'existing_image' in locals() else 0,
                "can_regenerate": not (is_regeneration and 'existing_image' in locals() and existing_image.regeneration_count >= 1)
            }
            
    except (CharacterNotFoundError, CharacterImageError) as e:
        # Re-raise known errors
        raise
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        raise CharacterImageError(
            message="Failed to generate image",
            details=str(e)
        )

@router.get("/check-name")
async def check_character_name(
    name: str = Query(..., description="Character name to check"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Check if a character name already exists for the current user and validate the name format.
    """
    try:
        # Validate name format
        if not name or not name.strip():
            raise HTTPException(
                status_code=422,
                detail={
                    "exists": False,
                    "valid": False,
                    "error": "Character name cannot be empty"
                }
            )
            
        if len(name) > 50:
            raise HTTPException(
                status_code=422,
                detail={
                    "exists": False,
                    "valid": False,
                    "error": "Character name cannot exceed 50 characters"
                }
            )
            
        # Check for valid character name pattern
        if not re.match(r'^[A-Za-z\s\'-]+$', name):
            raise HTTPException(
                status_code=422,
                detail={
                    "exists": False,
                    "valid": False,
                    "error": "Character name can only contain letters, spaces, hyphens, and apostrophes"
                }
            )
        
        # Check if name exists for current user
        existing_character = db.query(Character).filter(
            Character.user_id == current_user.id,
            Character.name == name
        ).first()
        
        if existing_character:
            raise HTTPException(
                status_code=409,  # Conflict for duplicate names
                detail={
                    "exists": True,
                    "valid": True,
                    "error": "Character name already exists"
                }
            )
        
        return {
            "exists": False,
            "valid": True,
            "error": None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking character name: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "exists": False,
                "valid": False,
                "error": "Failed to check character name"
            }
        )

@router.post("/{character_id}/enhance-prompt", response_model=CharacterResponse)
async def enhance_character_prompt(
    character_id: int,
    request: PromptEnhanceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    openai_client = Depends(get_openai_client)
):
    """
    Enhance a character's image generation prompt.
    """
    try:
        character = db.query(Character).filter(
            Character.id == character_id,
            Character.user_id == current_user.id
        ).first()
        
        if not character:
            raise CharacterNotFoundError(
                character_id=character_id,
                context=ErrorContext(
                    source="characters.enhance_character_prompt",
                    severity=ErrorSeverity.WARNING,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={"user_id": current_user.id}
                )
            )
        
        try:
            # Enhance the prompt using GPT-4
            enhanced_prompt = await enhance_image_prompt(
                openai_client,
                character.name,
                character.traits,
                request.base_prompt
            )
            
            # Update character's image prompt
            character.image_prompt = enhanced_prompt
            db.commit()
            
            return {"enhanced_prompt": enhanced_prompt}
        except Exception as e:
            db.rollback()
            raise CharacterUpdateError(
                message="Failed to enhance character prompt",
                context=ErrorContext(
                    source="characters.enhance_character_prompt",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "character_id": character_id,
                        "user_id": current_user.id,
                        "error": str(e)
                    }
                )
            )
            
    except Exception as e:
        if not isinstance(e, (CharacterNotFoundError, CharacterUpdateError)):
            raise CharacterError(
                message="Unexpected error enhancing character prompt",
                context=ErrorContext(
                    source="characters.enhance_character_prompt",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "character_id": character_id,
                        "user_id": current_user.id,
                        "error": str(e)
                    }
                )
            )
        raise

@router.post("/{character_id}/refine", response_model=CharacterResponse)
async def refine_character(
    character_id: int,
    request: CharacterRefineRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    openai_client = Depends(get_openai_client)
):
    """
    Refine a character's traits and regenerate images.
    """
    try:
        # Get the character
        character = db.query(Character).filter(
            Character.id == character_id,
            Character.user_id == current_user.id
        ).first()
        
        if not character:
            raise CharacterNotFoundError(character_id)
        
        # Update character traits
        character.traits = request.traits
        db.commit()
        
        # Initialize progress tracking
        generation_progress[character.id] = {
            "progress": 0,
            "images": [],
            "complete": False
        }
        
        # Define progress callback
        def progress_callback(progress: int, image_url: str = None):
            if image_url:
                if "images" not in generation_progress[character.id]:
                    generation_progress[character.id]["images"] = []
                generation_progress[character.id]["images"].append(image_url)
            generation_progress[character.id]["progress"] = progress
            logger.info(f"Progress update: {progress}/2, Image URL: {image_url if image_url else 'None'}")
        
        # Generate new images
        raw_image_urls = await generate_character_images(
            openai_client,
            character.name,
            character.traits,
            progress_callback=progress_callback
        )
        
        # Update character in database
        character.generated_images = raw_image_urls
        db.commit()
        
        return {"generated_images": raw_image_urls}
        
    except CharacterNotFoundError:
        # Re-raise known errors
        raise
    except Exception as e:
        logger.error(f"Error refining character: {str(e)}")
        raise CharacterImageError(
            message="Failed to refine character",
            details=str(e)
        )

@router.delete("/{character_id}")
async def delete_character(
    character_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a character by ID.
    """
    try:
        character = db.query(Character).filter(
            Character.id == character_id,
            Character.user_id == current_user.id
        ).first()
        
        if not character:
            raise CharacterNotFoundError(
                character_id=character_id,
                context=ErrorContext(
                    source="characters.delete_character",
                    severity=ErrorSeverity.WARNING,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={"user_id": current_user.id}
                )
            )
        
        try:
            db.delete(character)
            db.commit()
            return {"message": "Character deleted successfully"}
        except Exception as e:
            db.rollback()
            raise CharacterDeletionError(
                message="Failed to delete character",
                context=ErrorContext(
                    source="characters.delete_character",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "character_id": character_id,
                        "user_id": current_user.id,
                        "error": str(e)
                    }
                )
            )
            
    except Exception as e:
        if not isinstance(e, (CharacterNotFoundError, CharacterDeletionError)):
            raise CharacterError(
                message="Unexpected error deleting character",
                context=ErrorContext(
                    source="characters.delete_character",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "character_id": character_id,
                        "user_id": current_user.id,
                        "error": str(e)
                    }
                )
            )
        raise

@router.post("/generate-prompt")
async def generate_initial_prompt(
    data: dict,
    current_user: User = Depends(get_current_user),
    openai_client = Depends(get_openai_client)
):
    """
    Generate an initial image generation prompt based on character name and traits.
    """
    try:
        name = data.get("name")
        traits = data.get("traits", [])
        
        if not name or not traits:
            raise CharacterValidationError(
                message="Name and traits are required",
                context=ErrorContext(
                    source="characters.generate_initial_prompt",
                    severity=ErrorSeverity.WARNING,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "user_id": current_user.id,
                        "provided_name": name,
                        "provided_traits": traits
                    }
                )
            )
        
        # Generate base prompt
        base_prompt = f"Create a child-friendly character illustration for {name} with traits: {', '.join(traits)}"
        
        # Enhance the prompt using GPT-4
        enhanced_prompt = await enhance_image_prompt(
            openai_client,
            name,
            traits,
            base_prompt
        )
        
        return {"prompt": enhanced_prompt}
        
    except Exception as e:
        logger.error(f"Error generating initial prompt: {str(e)}")
        raise CharacterError(
            message="Failed to generate initial prompt",
            context=ErrorContext(
                source="characters.generate_initial_prompt",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={
                    "user_id": current_user.id,
                    "error": str(e)
                }
            )
        )

@router.post("/refine-prompt")
async def refine_prompt(
    data: dict,
    current_user: User = Depends(get_current_user),
    openai_client = Depends(get_openai_client)
):
    """
    Refine an image generation prompt using AI.
    """
    try:
        name = data.get("name")
        traits = data.get("traits", [])
        base_prompt = data.get("base_prompt")
        
        if not name or not traits or not base_prompt:
            raise CharacterValidationError(
                message="Name, traits, and base prompt are required",
                context=ErrorContext(
                    source="characters.refine_prompt",
                    severity=ErrorSeverity.WARNING,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "user_id": current_user.id,
                        "provided_name": name,
                        "provided_traits": traits,
                        "provided_prompt": base_prompt
                    }
                )
            )
        
        # Enhance the prompt using GPT-4
        enhanced_prompt = await enhance_image_prompt(
            openai_client,
            name,
            traits,
            base_prompt
        )
        
        return {"enhanced_prompt": enhanced_prompt}
        
    except Exception as e:
        logger.error(f"Error refining prompt: {str(e)}")
        raise CharacterError(
            message="Failed to refine prompt",
            context=ErrorContext(
                source="characters.refine_prompt",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={
                    "user_id": current_user.id,
                    "error": str(e)
                }
            )
        ) 