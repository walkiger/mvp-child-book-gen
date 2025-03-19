# app/api/dependencies.py

"""
Common dependencies for authentication and other purposes.
"""

from typing import Generator
from datetime import datetime, UTC
from uuid import uuid4
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt
from jwt.exceptions import PyJWTError

from app.config import get_settings
from app.database import models
from app.database.session import get_db
from app.core.errors.auth import AuthenticationError
from app.core.errors.base import ErrorContext, ErrorSeverity

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    """
    Get the current user from the token.

    Args:
        token (str): The JWT access token.
        db (Session): The database session.

    Returns:
        models.User: The authenticated user.

    Raises:
        AuthenticationError: If the token is invalid or user not found.
    """
    try:
        settings = get_settings()
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email: str = payload.get("sub")
        if email is None:
            error_context = ErrorContext(
                source="dependencies.get_current_user",
                severity=ErrorSeverity.WARNING,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={
                    "reason": "Missing email in token payload"
                }
            )
            raise AuthenticationError(
                message="Could not validate credentials",
                error_code="AUTH-TOKEN-001",
                context=error_context
            )
    except PyJWTError as e:
        error_context = ErrorContext(
            source="dependencies.get_current_user",
            severity=ErrorSeverity.WARNING,
            timestamp=datetime.now(UTC),
            error_id=str(uuid4()),
            additional_data={
                "error": str(e)
            }
        )
        raise AuthenticationError(
            message="Could not validate credentials",
            error_code="AUTH-TOKEN-002",
            context=error_context
        )

    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        error_context = ErrorContext(
            source="dependencies.get_current_user",
            severity=ErrorSeverity.WARNING,
            timestamp=datetime.now(UTC),
            error_id=str(uuid4()),
            additional_data={
                "email": email
            }
        )
        raise AuthenticationError(
            message="Could not validate credentials",
            error_code="AUTH-USER-001",
            context=error_context
        )

    return user
