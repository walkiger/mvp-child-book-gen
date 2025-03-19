"""
Core authentication functionality.
"""

from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from argon2 import PasswordHasher, exceptions as argon2_exceptions
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging
from uuid import uuid4

from app.config import get_settings, Settings
from app.database.models import User
from app.database.session import get_db
from app.core.errors.auth import (
    AuthError,
    AuthenticationError,
    AuthorizationError,
    TokenError,
    SessionError
)
from app.core.errors.base import ErrorContext, ErrorSeverity
from app.schemas.auth import UserResponse
from app.schemas.user import UserCreate

logger = logging.getLogger(__name__)

# Initialize Argon2 password hasher with recommended parameters
ph = PasswordHasher(
    time_cost=2,        # Number of iterations
    memory_cost=102400, # Memory usage in KiB (100 MB)
    parallelism=8,      # Number of parallel threads
    hash_len=32,        # Length of the hash in bytes
    salt_len=16         # Length of the random salt in bytes
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password using Argon2.
    """
    try:
        return ph.verify(hashed_password, plain_password)
    except argon2_exceptions.VerifyMismatchError:
        return False
    except argon2_exceptions.VerificationError:
        return False

def get_password_hash(password: str) -> str:
    """
    Hash a password using Argon2.
    """
    return ph.hash(password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, get_settings().secret_key, algorithm="HS256")
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> UserResponse:
    """
    Get the current user from the JWT token.
    """
    try:
        payload = jwt.decode(token, get_settings().secret_key, algorithms=["HS256"])
        email: str = payload.get("sub")
        if email is None:
            raise TokenError(
                message="Could not validate credentials",
                error_code="AUTH-TOKEN-MISS-001",
                context=ErrorContext(
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4())
                )
            )
    except JWTError:
        raise TokenError(
            message="Invalid or expired token",
            error_code="AUTH-TOKEN-INV-001",
            context=ErrorContext(
                timestamp=datetime.now(UTC),
                error_id=str(uuid4())
            )
        )

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise AuthenticationError(
            message=f"User not found: {email}",
            error_code="AUTH-USER-NFD-001",
            context=ErrorContext(
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"email": email}
            )
        )

    return UserResponse.model_validate(user)

async def get_current_admin_user(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    """
    Check if the current user is an admin.
    Raises a 403 Forbidden exception if the user is not an admin.
    """
    if not current_user.is_admin:
        raise AuthorizationError(
            message="Admin access required",
            required_permission="admin",
            error_code="AUTH-PERM-ADM-001",
            context=ErrorContext(
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                user_id=str(current_user.id)
            )
        )
    return current_user

async def authenticate_user(email: str, password: str, db: Session) -> Optional[User]:
    """Authenticate a user by email and password."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise AuthenticationError(
            message="Invalid email or password",
            error_code="AUTH-CRED-INV-001",
            context=ErrorContext(
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"email": email}
            )
        )
    if not verify_password(password, user.password_hash):
        raise AuthenticationError(
            message="Invalid email or password",
            error_code="AUTH-CRED-INV-001",
            context=ErrorContext(
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"email": email}
            )
        )
    return user

async def register_user(user_data: dict, db: Session) -> User:
    """Register a new user."""
    try:
        logger.info(f"Registration attempt for email: {user_data['email']}")

        # Check if email exists
        if db.query(User).filter(User.email == user_data['email']).first():
            logger.warning(f"User already exists with email: {user_data['email']}")
            raise AuthenticationError(
                message="Email already exists",
                error_code="AUTH-REG-DUP-001",
                context=ErrorContext(
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={"email": user_data['email']}
                )
            )

        # Check if username exists
        if db.query(User).filter(User.username == user_data['username']).first():
            logger.warning(f"Username already taken: {user_data['username']}")
            raise AuthenticationError(
                message="Username already exists",
                error_code="AUTH-REG-DUP-002",
                context=ErrorContext(
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={"username": user_data['username']}
                )
            )

        # Create password hash
        password_hash = get_password_hash(user_data['password'])

        # Create new user
        user = User(
            email=user_data['email'],
            username=user_data['username'],
            password_hash=password_hash,
            first_name=user_data.get('first_name', ''),
            last_name=user_data.get('last_name', '')
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        logger.info(f"Successfully registered user: {user.email}")
        return user

    except IntegrityError as e:
        logger.error(f"Database error during registration: {str(e)}")
        db.rollback()
        raise AuthenticationError(
            message="Registration failed",
            error_code="AUTH-REG-DB-001",
            context=ErrorContext(
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={
                    "email": user_data['email'],
                    "error": str(e)
                }
            )
        )
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}")
        db.rollback()
        raise AuthError(
            message="Registration failed",
            error_code="AUTH-REG-ERR-001",
            context=ErrorContext(
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={
                    "email": user_data['email'],
                    "error": str(e)
                }
            )
        )

async def register(user_data: UserCreate, db: Session) -> User:
    """Register a new user."""
    # Check if user with email already exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise AuthenticationError(
            message="Email already registered",
            error_code="AUTH-REG-DUP-001",
            context=ErrorContext(
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"email": user_data.email}
            )
        )

    # Create new user
    user = User(
        email=user_data.email,
        username=user_data.username,
        password_hash=get_password_hash(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError as e:
        db.rollback()
        raise AuthenticationError(
            message="Registration failed",
            error_code="AUTH-REG-DB-001",
            context=ErrorContext(
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={
                    "email": user_data.email,
                    "error": str(e)
                }
            )
        ) 