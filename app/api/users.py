# app/api/users.py

"""
API endpoints for user-related operations, including profile management,
password change, and account deletion.
"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    status,
    Response,
)
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from app.database.engine import SessionLocal
from app.database import models
from app.schemas import user as schemas
from app.api.auth import get_current_user, authenticate_user
from app.database.utils import hash_password, verify_password
from app.api.auth import get_db  # Reuse the get_db dependency
from PIL import Image
import io

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


def get_db():
    """
    Dependency that provides a database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/me", response_model=schemas.UserResponse)
def get_profile(
    current_user: models.User = Depends(get_current_user),
):
    """
    Retrieve the current user's profile information.

    Args:
        current_user (models.User): The currently authenticated user.

    Returns:
        UserResponse: The current user's profile data.
    """
    return current_user


@router.put("/me", response_model=schemas.UserResponse)
def update_profile(
    user_update: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update the current user's profile information.

    Args:
        user_update (UserUpdate): The fields to update.
        current_user (models.User): The currently authenticated user.
        db (Session): The database session.

    Returns:
        UserResponse: The updated user profile.
    """
    update_data = user_update.dict(exclude_unset=True)

    # Prevent updating email and username here to avoid conflicts
    forbidden_fields = {"email", "username", "password"}
    if forbidden_fields.intersection(update_data.keys()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update email, username, or password via this endpoint.",
        )

    for field, value in update_data.items():
        setattr(current_user, field, value)

    try:
        db.add(current_user)
        db.commit()
        db.refresh(current_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An error occurred while updating your profile.",
        )

    return current_user


@router.put("/me/password", response_model=schemas.Message)
def change_password(
    password_data: schemas.PasswordChange,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Change the current user's password.

    Args:
        password_data (PasswordChange): The old and new passwords.
        current_user (models.User): The currently authenticated user.
        db (Session): The database session.

    Returns:
        Message: A success message.
    """
    if not verify_password(password_data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old password is incorrect.",
        )

    current_user.password_hash = hash_password(password_data.new_password)
    db.add(current_user)
    db.commit()
    return {"detail": "Password changed successfully."}


@router.delete("/me", response_model=schemas.Message)
def delete_account(
    password_data: schemas.PasswordDelete,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete the current user's account.

    Args:
        password_data (PasswordDelete): The user's password for confirmation.
        current_user (models.User): The currently authenticated user.
        db (Session): The database session.

    Returns:
        Message: A success message upon account deletion.
    """
    # Verify password for security
    if not verify_password(password_data.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is incorrect.",
        )

    db.delete(current_user)
    db.commit()
    return {"detail": "Account deleted successfully."}


@router.get("/{user_id}", response_model=schemas.UserPublic)
def get_user_profile(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Retrieve another user's public profile information.

    Args:
        user_id (int): The ID of the user to retrieve.
        db (Session): The database session.
        current_user (models.User): The currently authenticated user.

    Returns:
        UserPublic: The user's public profile data.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return user


@router.get("/", response_model=List[schemas.UserPublic])
def list_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    List all users.

    Args:
        db (Session): The database session.
        current_user (models.User): The currently authenticated user.

    Returns:
        List[UserPublic]: A list of users' public profiles.
    """
    # Implement access control if necessary
    users = db.query(models.User).all()
    return users


@router.post("/avatar", response_model=schemas.UserResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload and update the user's avatar.

    The image will be resized to 100x100 pixels to ensure consistent dimensions
    and optimize storage.

    Args:
        file (UploadFile): The uploaded image file.
        current_user (models.User): The currently authenticated user.
        db (Session): The database session.

    Returns:
        UserResponse: The updated user profile.
    """
    # Validate file type
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only JPEG and PNG are allowed.",
        )

    # Read file data
    image_data = await file.read()

    # Enforce maximum file size (e.g., 1 MB)
    MAX_FILE_SIZE = 1 * 1024 * 1024  # 1 MB
    if len(image_data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds the maximum limit of 1 MB.",
        )

    try:
        # Open the image using Pillow
        image = Image.open(io.BytesIO(image_data))

        # Resize the image to 100x100 pixels
        image = image.convert("RGB")  # Ensure image is in RGB format
        image = image.resize((100, 100), Image.ANTIALIAS)

        # Save the resized image to a bytes buffer
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        resized_image_data = buffer.getvalue()
        buffer.close()

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error processing image.",
        )

    # Update user's avatar and content type
    current_user.avatar = resized_image_data
    current_user.avatar_content_type = "image/jpeg"  # Since we saved as JPEG
    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return current_user


@router.get("/avatar")
def get_avatar(
    current_user: models.User = Depends(get_current_user),
):
    """
    Retrieve the current user's avatar image.

    Returns:
        Response: The avatar image data with the appropriate content type.
    """
    if not current_user.avatar or not current_user.avatar_content_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User avatar not found.",
        )

    return Response(
        content=current_user.avatar,
        media_type=current_user.avatar_content_type,
    )


@router.get("/{user_id}/avatar")
def get_user_avatar(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieve another user's avatar image.

    Args:
        user_id (int): The ID of the user.

    Returns:
        Response: The avatar image data with the appropriate content type.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or not user.avatar or not user.avatar_content_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User avatar not found.",
        )

    return Response(
        content=user.avatar,
        media_type=user.avatar_content_type,
    )
