"""
Image serving API endpoints.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.core.auth import get_current_user
from app.database.models import User, Image
from app.database.session import get_db

router = APIRouter(tags=["images"])

@router.get("/{image_id}")
async def get_image(
    image_id: int,
    db: Session = Depends(get_db)
):
    """
    Get an image by ID and serve it with the correct content type.
    """
    # Find the image in the database
    image = db.query(Image).filter(Image.id == image_id).first()
    
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Determine content type
    content_type = f"image/{image.image_format}"
    
    # Return the image with proper content type
    return Response(content=image.image_data, media_type=content_type) 