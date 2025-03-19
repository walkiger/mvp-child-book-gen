# app/core/security.py

"""
Security utilities for handling password hashing and JWT tokens.
"""

from datetime import datetime, timedelta, UTC
from jose import jwt, JWTError
from argon2 import PasswordHasher, exceptions as argon2_exceptions
from app.config import get_settings
from typing import Optional, Dict
from uuid import uuid4

from app.core.errors.auth import TokenError, AuthError
from app.core.errors.base import ErrorContext

# Password hasher
ph = PasswordHasher()

# Get settings
settings = get_settings()
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time delta

    Returns:
        str: Encoded JWT token

    Raises:
        TokenError: If token creation fails
    """
    try:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        raise TokenError(
            message="Failed to create access token",
            error_code="AUTH-TOKEN-CREATE-001",
            context=ErrorContext(
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"error": str(e)}
            )
        )


def get_password_hash(password: str) -> str:
    """
    Hash a password using Argon2.

    Args:
        password: Plain text password

    Returns:
        str: Hashed password

    Raises:
        AuthError: If password hashing fails
    """
    try:
        return ph.hash(password)
    except argon2_exceptions.HashingError as e:
        raise AuthError(
            message="Failed to hash password",
            error_code="AUTH-HASH-FAIL-001",
            context=ErrorContext(
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"error": str(e)}
            )
        )


def verify_token(token: str) -> Dict:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token to verify

    Returns:
        Dict: Decoded token payload

    Raises:
        TokenError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise TokenError(
            message="Invalid or expired token",
            error_code="AUTH-TOKEN-INV-001",
            context=ErrorContext(
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"error": str(e)}
            )
        )
    except Exception as e:
        raise TokenError(
            message="Failed to verify token",
            error_code="AUTH-TOKEN-VERIFY-001",
            context=ErrorContext(
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"error": str(e)}
            )
        )
