"""
Image serving API endpoints.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.core.auth import get_current_user
from app.database.models import User, Image
from app.database.session import get_db
from app.core.image_errors import (
    ImageNotFoundError,
    ImageFormatError,
    ImageProcessingError,
    ImageStorageError,
    ImageValidationError
)
from app.core.error_handling import setup_logger

# Set up logger
logger = setup_logger("images", "logs/images.log")

router = APIRouter(tags=["images"])

@router.get("/{image_id}")
async def get_image(
    image_id: int,
    db: Session = Depends(get_db)
):
    """
    Get an image by ID and serve it with the correct content type.
    """
    try:
        # Find the image in the database
        image = db.query(Image).filter(Image.id == image_id).first()
        
        if not image:
            raise ImageNotFoundError(image_id)
        
        try:
            # Determine content type
            content_type = f"image/{image.image_format}"
            
            # Return the image with proper content type
            return Response(content=image.image_data, media_type=content_type)
        except Exception as e:
            logger.error(f"Error processing image {image_id}: {str(e)}")
            raise ImageProcessingError(
                message="Failed to process image",
                details=str(e)
            )
            
    except ImageNotFoundError:
        # Re-raise known errors
        raise
    except Exception as e:
        logger.error(f"Error retrieving image {image_id}: {str(e)}")
        raise ImageNotFoundError(
            image_id=image_id,
            details=str(e)
        ) 