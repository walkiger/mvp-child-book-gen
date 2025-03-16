"""
Character management API endpoints.
"""

from typing import List, Dict, Any, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.orm import Session
from app.core.auth import get_current_user
from app.database.models import User, Character, Image
from app.database.session import get_db
from app.schemas.character import CharacterCreate, CharacterResponse, CharacterUpdate, CharacterImageGenerationProgress, PromptEnhanceRequest
from app.core.image_generation import generate_character_images
from app.core.openai_client import get_openai_client
from app.core.rate_limiter import check_rate_limit
import asyncio
import json
import httpx
import io
import os
from datetime import datetime

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
    character: CharacterCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new character with generated images.
    """
    print("Starting character creation...")
    
    # Get DALL-E version from request or use default
    dalle_version = getattr(character, 'dalle_version', 'dall-e-3')
    
    # Create character in database first
    db_character = Character(
        user_id=current_user.id,
        name=character.name,
        traits=character.traits,
        image_prompt=f"Create a child-friendly character illustration for {character.name} with traits: {', '.join(character.traits)}"
    )
    
    print("Adding character to database...")
    db.add(db_character)
    db.commit()
    db.refresh(db_character)
    print(f"Character created with ID: {db_character.id}")
    
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
        print(f"Progress update: {progress}/2, Image URL: {image_url if image_url else 'None'}")
    
    # Generate images using DALL-E with progress updates
    print("Initializing OpenAI client...")
    openai_client = get_openai_client()
    
    print("Starting image generation...")
    try:
        # Get the raw image URLs from OpenAI
        raw_image_urls = await generate_character_images(
            openai_client,
            character.name,
            character.traits,
            dalle_version=dalle_version,
            progress_callback=progress_callback
        )
        print(f"Successfully generated {len(raw_image_urls)} images")
        
        # Download and store the images
        stored_image_paths = []
        for i, image_url in enumerate(raw_image_urls):
            try:
                # Download the image
                async with httpx.AsyncClient() as client:
                    response = await client.get(image_url)
                    if response.status_code != 200:
                        print(f"Failed to download image {i}: status code {response.status_code}")
                        continue
                    
                    # Get image data and format
                    image_data = response.content
                    content_type = response.headers.get("content-type", "")
                    image_format = content_type.split("/")[-1] if "/" in content_type else "png"
                    
                    # Create new image record in database
                    db_image = Image(
                        character_id=db_character.id,
                        image_data=image_data,
                        image_format=image_format,
                        dalle_version=dalle_version,
                        generation_cost=0.02 if dalle_version == "dall-e-3" else 0.01,  # Estimate cost
                    )
                    db.add(db_image)
                    db.commit()
                    db.refresh(db_image)
                    
                    # Store reference to our database image
                    stored_image_paths.append(f"/api/images/{db_image.id}")
            except Exception as e:
                print(f"Error processing image {i}: {str(e)}")
                # Use the raw URL as fallback
                stored_image_paths.append(image_url)
        
        # Update progress
        generation_progress[db_character.id]["complete"] = True
        generation_progress[db_character.id]["images"] = stored_image_paths
        
        # Update the character with generated images
        print("Updating character with generated images...")
        db_character.generated_images = stored_image_paths
        
        # Set the first image as the default image path
        if stored_image_paths:
            db_character.image_path = stored_image_paths[0]
            
        db.commit()
        db.refresh(db_character)
        
    except Exception as e:
        print(f"Error during image generation: {str(e)}")
        raise
    
    return db_character


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
    character = db.query(Character).filter(
        Character.id == character_id,
        Character.user_id == current_user.id
    ).first()
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    if not character.generated_images:
        raise HTTPException(status_code=400, detail="No generated images available")
    
    # Get the image index from the request
    image_index = data.get("image_index")
    if image_index is None:
        raise HTTPException(status_code=400, detail="Image index is required")
    
    try:
        image_index = int(image_index)
    except ValueError:
        raise HTTPException(status_code=400, detail="Image index must be a number")
    
    # Check if the index is valid
    if image_index < 0 or image_index >= len(character.generated_images):
        raise HTTPException(status_code=400, detail="Invalid image index")
    
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


@router.post("/{character_id}/regenerate")
async def regenerate_character_images(
    character_id: int,
    data: dict = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Regenerate character images (allowed once per character).
    
    Parameters:
    - dalle_version: The DALL-E version to use ('dall-e-2' or 'dall-e-3')
    """
    character = db.query(Character).filter(
        Character.id == character_id,
        Character.user_id == current_user.id
    ).first()
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Get DALL-E version from request or use default
    dalle_version = data.get("dalle_version", "dall-e-3")
    
    # Generate new images
    openai_client = get_openai_client()
    images = await generate_character_images(
        openai_client, 
        character.name, 
        character.traits,
        dalle_version=dalle_version
    )
    
    # Update character in database
    character.generated_images = images
    db.commit()
    
    return {"generated_images": images}


@router.get("/", response_model=List[CharacterResponse])
async def get_user_characters(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all characters for the current user.
    """
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


@router.get("/{character_id}", response_model=CharacterResponse)
async def get_character(
    character_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific character by ID.
    """
    character = db.query(Character).filter(
        Character.id == character_id,
        Character.user_id == current_user.id
    ).first()
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    return {
        "id": character.id,
        "user_id": character.user_id,
        "name": character.name,
        "traits": character.traits,
        "image_path": character.image_path,
        "generated_images": character.generated_images
    }

@router.put("/{character_id}", response_model=CharacterResponse)
async def update_character(
    character_id: int,
    character_data: CharacterUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a character by ID.
    """
    # Find the character
    character = db.query(Character).filter(
        Character.id == character_id,
        Character.user_id == current_user.id
    ).first()
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Update character fields
    if character_data.name is not None:
        character.name = character_data.name
    
    if character_data.traits is not None:
        character.traits = character_data.traits
    
    if character_data.image_path is not None:
        character.image_path = character_data.image_path
    
    if character_data.image_prompt is not None:
        character.image_prompt = character_data.image_prompt
        
    # Save changes
    db.commit()
    db.refresh(character)
    
    return {
        "id": character.id,
        "user_id": character.user_id,
        "name": character.name,
        "traits": character.traits,
        "image_path": character.image_path,
        "generated_images": character.generated_images
    }

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
    # Apply rate limiting
    if not check_rate_limit("image_generation", current_user.id):
        raise HTTPException(
            status_code=429, 
            detail="Rate limit exceeded for image generation. Please try again later."
        )
        
    character = db.query(Character).filter(
        Character.id == character_id,
        Character.user_id == current_user.id
    ).first()
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
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
                raise HTTPException(
                    status_code=403,
                    detail="Maximum image regeneration limit reached. Each image can only be regenerated once."
                )
    
    # Use provided prompt or character's default prompt
    prompt = custom_prompt or character.image_prompt or f"Create a child-friendly character illustration for {character.name} with traits: {', '.join(character.traits)}"
    
    try:
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
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to download generated image: {img_response.status_code}"
                )
                
            # Get image data and format
            image_data = img_response.content
            content_type = img_response.headers.get("content-type", "")
            image_format = content_type.split("/")[-1] if "/" in content_type else "png"
            
            # If this is a regeneration, update the existing image's regeneration count
            if is_regeneration and 'existing_image' in locals() and existing_image:
                existing_image.regeneration_count += 1
                existing_image.image_data = image_data
                existing_image.image_format = image_format
                existing_image.dalle_version = dalle_version
                existing_image.generation_cost += 0.02 if dalle_version == "dall-e-3" else 0.01
                existing_image.generated_at = datetime.utcnow()
                db.commit()
                db.refresh(existing_image)
                
                # Use the same image path
                image_path = f"/api/images/{existing_image.id}"
            else:
                # Create new image record in database
                db_image = Image(
                    character_id=character_id,
                    image_data=image_data,
                    image_format=image_format,
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
            
    except Exception as e:
        print(f"Error generating image: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate image: {str(e)}"
        )

@router.get("/check-name", response_model=dict)
async def check_character_name_exists(
    name: str = Query(..., description="Character name to check"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if a character with the given name already exists for the current user.
    
    Returns:
        dict: {"exists": boolean} - True if character name exists, False otherwise
    """
    existing_character = db.query(Character).filter(
        Character.user_id == current_user.id,
        Character.name == name
    ).first()
    
    return {"exists": existing_character is not None}

@router.post("/enhance-prompt", response_model=dict)
async def enhance_prompt(
    request: PromptEnhanceRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Enhance a character prompt using GPT for better image generation results.
    
    Returns:
        dict: {"enhanced_prompt": str} - The enhanced prompt
    """
    try:
        # Get OpenAI client
        client = get_openai_client()
        
        # Build system message with instructions
        system_message = """
        You are an expert at crafting perfect prompts for DALL-E to create beautiful character illustrations.
        Your task is to enhance the provided character prompt to create a more detailed, descriptive 
        and visually compelling character description that will result in better DALL-E images.
        
        Follow these guidelines:
        1. Keep the prompt child-friendly and appropriate
        2. Maintain the core character traits provided
        3. Add more visual details like clothing, expressions, poses, backgrounds
        4. Specify art style that would appeal to children (e.g., Pixar-like, Disney-inspired, watercolor)
        5. Keep the enhanced prompt under 1000 characters
        6. Focus on positive and uplifting descriptions
        7. Don't change the character's name or core concept
        """
        
        # Build the user message with the base prompt and character details
        user_message = f"""
        Character Name: {request.name}
        Character Traits: {', '.join(request.traits)}
        Base Prompt: {request.base_prompt}
        
        Please enhance this prompt to create a better character visualization while maintaining the core character traits.
        """
        
        # Call OpenAI API
        response = await client.chat.completions.create(
            model="gpt-4",  # Use GPT-4 for better prompt engineering
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        # Extract the enhanced prompt
        enhanced_prompt = response.choices[0].message.content.strip()
        
        return {"enhanced_prompt": enhanced_prompt}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to enhance prompt: {str(e)}"
        )

@router.delete("/{character_id}")
async def delete_character(
    character_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a character by ID.
    
    Returns:
        dict: {"success": boolean, "message": str} - Result of the delete operation
    """
    # Find the character
    character = db.query(Character).filter(
        Character.id == character_id,
        Character.user_id == current_user.id
    ).first()
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Delete associated images
    images = db.query(Image).filter(Image.character_id == character_id).all()
    for image in images:
        db.delete(image)
    
    # Delete the character
    db.delete(character)
    db.commit()
    
    return {
        "success": True,
        "message": f"Character '{character.name}' and associated images deleted successfully"
    } 