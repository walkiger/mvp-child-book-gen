# app/api/users.py

"""
API endpoints for user-related operations, including profile management,
password change, and account deletion.
"""

from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    status,
    Response,
)
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from datetime import datetime, UTC
from uuid import uuid4
from PIL import Image
import io
import logging

from app.database import models
from app.schemas import user as schemas
from app.api.dependencies import get_current_user, get_db
from app.database.utils import hash_password, verify_password
from app.core.errors.user import (
    UserError,
    UserNotFoundError,
    UserValidationError,
    UserProfileError
)
from app.core.errors.base import ErrorContext

logger = logging.getLogger(__name__)

router = APIRouter(tags=["users"])


@router.get("/me", response_model=schemas.UserResponse)
def get_profile(current_user: models.User = Depends(get_current_user)):
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
    update_data = user_update.model_dump(exclude_unset=True)

    # Validate forbidden fields
    forbidden_fields = {"email", "username", "password"}
    if forbidden_fields.intersection(update_data.keys()):
        raise UserValidationError(
            message="Cannot update protected fields",
            error_code="USER-VAL-FIELD-001",
            context=ErrorContext(
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                user_id=str(current_user.id),
                additional_data={"forbidden_fields": list(forbidden_fields.intersection(update_data.keys()))}
            )
        )

    try:
        for field, value in update_data.items():
            setattr(current_user, field, value)

        db.add(current_user)
        db.commit()
        db.refresh(current_user)
        return current_user
    except IntegrityError as e:
        db.rollback()
        raise UserProfileError(
            message="Failed to update profile",
            error_code="USER-PROF-UPD-001",
            context=ErrorContext(
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                user_id=str(current_user.id),
                additional_data={"error": str(e)}
            )
        )


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
        raise UserValidationError(
            message="Old password is incorrect",
            error_code="USER-VAL-PWD-001",
            context=ErrorContext(
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                user_id=str(current_user.id)
            )
        )

    try:
        current_user.password_hash = hash_password(password_data.new_password)
        db.add(current_user)
        db.commit()
        return {"detail": "Password changed successfully."}
    except Exception as e:
        db.rollback()
        raise UserProfileError(
            message="Failed to update password",
            error_code="USER-PROF-PWD-001",
            context=ErrorContext(
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                user_id=str(current_user.id),
                additional_data={"error": str(e)}
            )
        )


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
    if not verify_password(password_data.password, current_user.password_hash):
        raise UserValidationError(
            message="Password is incorrect",
            error_code="USER-VAL-PWD-001",
            context=ErrorContext(
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                user_id=str(current_user.id)
            )
        )

    try:
        db.delete(current_user)
        db.commit()
        return {"detail": "Account deleted successfully."}
    except Exception as e:
        db.rollback()
        raise UserProfileError(
            message="Failed to delete account",
            error_code="USER-PROF-DEL-001",
            context=ErrorContext(
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                user_id=str(current_user.id),
                additional_data={"error": str(e)}
            )
        )


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
        raise UserNotFoundError(
            message=f"User not found: {user_id}",
            error_code="USER-NFD-ID-001",
            context=ErrorContext(
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                user_id=str(current_user.id),
                additional_data={"requested_user_id": user_id}
            )
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
    return db.query(models.User).all()


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
        raise UserValidationError(
            message="Invalid file type",
            error_code="USER-VAL-IMG-001",
            context=ErrorContext(
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                user_id=str(current_user.id),
                additional_data={
                    "content_type": file.content_type,
                    "allowed_types": ["image/jpeg", "image/png"]
                }
            )
        )

    try:
        # Read file data
        image_data = await file.read()

        # Enforce maximum file size
        MAX_FILE_SIZE = 1 * 1024 * 1024  # 1 MB
        if len(image_data) > MAX_FILE_SIZE:
            raise UserValidationError(
                message="File size exceeds limit",
                error_code="USER-VAL-IMG-002",
                context=ErrorContext(
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    user_id=str(current_user.id),
                    additional_data={
                        "file_size": len(image_data),
                        "max_size": MAX_FILE_SIZE
                    }
                )
            )

        # Process image
        image = Image.open(io.BytesIO(image_data))
        image = image.convert("RGB")
        image = image.resize((100, 100), Image.ANTIALIAS)

        # Save the resized image
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        resized_image_data = buffer.getvalue()
        buffer.close()

        # Update user's avatar
        current_user.avatar = resized_image_data
        current_user.avatar_content_type = "image/jpeg"
        db.add(current_user)
        db.commit()
        db.refresh(current_user)

        return current_user
    except Exception as e:
        db.rollback()
        raise UserProfileError(
            message="Failed to update avatar",
            error_code="USER-PROF-IMG-001",
            context=ErrorContext(
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                user_id=str(current_user.id),
                additional_data={"error": str(e)}
            )
        )


@router.get("/avatar")
def get_avatar(current_user: models.User = Depends(get_current_user)):
    """
    Retrieve the current user's avatar image.

    Returns:
        Response: The avatar image data with the appropriate content type.
    """
    if not current_user.avatar or not current_user.avatar_content_type:
        raise UserNotFoundError(
            message="User avatar not found",
            error_code="USER-NFD-IMG-001",
            context=ErrorContext(
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                user_id=str(current_user.id)
            )
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
        raise UserNotFoundError(
            message="User avatar not found",
            error_code="USER-NFD-IMG-001",
            context=ErrorContext(
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"user_id": user_id}
            )
        )

    return Response(
        content=user.avatar,
        media_type=user.avatar_content_type,
    )
