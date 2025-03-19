"""
Image serving API endpoints.
"""

from typing import Optional
from datetime import datetime, UTC
from uuid import uuid4
from fastapi import APIRouter, Depends, Body, Response, Request
from sqlalchemy.orm import Session
from app.core.auth import get_current_user
from app.database.session import get_db
from app.database.models import User, Image
from app.core.openai_client import get_openai_client
from app.core.image_generation import call_openai_image_api, enhance_image_prompt
from app.core.logging import setup_logger
from app.core.errors.image import ImageGenerationError, ImageValidationError, ImageError
from app.core.errors.base import ErrorContext, ErrorSeverity
from app.schemas.character import PromptEnhanceRequest
from fastapi.responses import JSONResponse
from app.core.rate_limiter import rate_limiter

# Set up logger
logger = setup_logger("images", "logs/images.log")

router = APIRouter(
    tags=["images"]
)

@router.post("/enhance-prompt")
async def enhance_prompt(
    request: Request,
    prompt_request: PromptEnhanceRequest,
    openai_client = Depends(get_openai_client)
):
    """
    Enhance a base prompt using GPT-4.
    """
    try:
        # Check OpenAI rate limits before making the API call
        rate_limiter.check_rate_limit(request, "openai_chat")

        enhanced_prompt = await enhance_image_prompt(
            openai_client,
            prompt_request.name,
            prompt_request.traits,
            prompt_request.base_prompt
        )
        return {"enhanced_prompt": enhanced_prompt}
    except Exception as e:
        logger.error(f"Error enhancing prompt: {str(e)}")
        error_context = ErrorContext(
            source="images.enhance_prompt",
            severity=ErrorSeverity.ERROR,
            timestamp=datetime.now(UTC),
            error_id=str(uuid4()),
            additional_data={
                "name": prompt_request.name,
                "traits": prompt_request.traits,
                "base_prompt": prompt_request.base_prompt,
                "error": str(e)
            }
        )
        raise ImageValidationError(
            message="Failed to enhance image prompt",
            validation_type="prompt_enhancement",
            issue=str(e),
            context=error_context
        )

@router.post("/generate", status_code=201)
async def generate_image(
    request: Request,
    prompt: str = Body(...),
    style: Optional[str] = Body(None),
    openai_client = Depends(get_openai_client)
):
    """
    Generate an image using DALL-E.
    """
    try:
        # Check OpenAI rate limits before making the API call
        rate_limiter.check_rate_limit(request, "openai_image")

        image_url = await call_openai_image_api(
            openai_client,
            "dall-e-3",
            prompt,
            "1024x1024",
            "standard",
            1,
            style
        )
        return {"url": image_url}
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        error_context = ErrorContext(
            source="images.generate_image",
            severity=ErrorSeverity.ERROR,
            timestamp=datetime.now(UTC),
            error_id=str(uuid4()),
            additional_data={
                "prompt": prompt,
                "style": style,
                "model": "dall-e-3",
                "error": str(e)
            }
        )
        raise ImageGenerationError(
            message="Failed to generate image",
            generation_step="dall-e-api-call",
            error_code="IMG-GEN-FAIL-001",
            context=error_context
        )

@router.get("/{image_id}")
async def get_image(
    image_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get an image by ID.
    """
    try:
        # Query the image
        image = db.query(Image).filter(Image.id == image_id).first()
        
        if not image:
            raise ImageError(
                message="Image not found",
                error_code="IMG-NOT-FOUND",
                http_status_code=404,
                context=ErrorContext(
                    source="images.get_image",
                    severity=ErrorSeverity.WARNING,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={"image_id": image_id}
                )
            )
        
        # Check if user has access to this image
        if image.user_id != current_user.id:
            raise ImageError(
                message="Not authorized to access this image",
                error_code="IMG-AUTH-002",
                http_status_code=403,
                context=ErrorContext(
                    source="images.get_image",
                    severity=ErrorSeverity.WARNING,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "image_id": image_id,
                        "user_id": current_user.id,
                        "image_owner_id": image.user_id
                    }
                )
            )
        
        # Return the image data with proper content type
        content_type = f"image/{image.format}" if image.format else "image/png"
        return Response(
            content=image.data,
            media_type=content_type
        )
        
    except Exception as e:
        if isinstance(e, ImageError):
            raise
        logger.error(f"Error retrieving image: {str(e)}")
        raise ImageError(
            message="Failed to retrieve image",
            error_code="IMG-RETRIEVE-ERR",
            http_status_code=500,
            context=ErrorContext(
                source="images.get_image",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={
                    "image_id": image_id,
                    "error": str(e)
                }
            )
        )