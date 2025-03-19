# app/api/auth.py

"""
Authentication API endpoints.
"""

from datetime import timedelta, datetime, UTC
from typing import Any
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from fastapi.responses import JSONResponse
import logging

from app.core.auth import (
    get_current_user,
    create_access_token,
    verify_password,
    get_password_hash,
    TokenError
)
from app.core.security import verify_token
from app.database.models import User
from app.database.session import get_db
from app.schemas.auth import Token, UserCreate, UserResponse
from app.schemas.user import TokenData, LoginRequest
from app.config import get_settings
from app.core.errors.auth import (
    AuthenticationError,
    RegistrationError,
    AuthorizationError
)
from app.core.errors.user import UserValidationError, UserNotFoundError
from app.core.errors.base import ErrorContext, ErrorSeverity
from app.core.logging import setup_logger

# Set up logger
logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


@router.post("/register", response_model=Token, status_code=201)
async def register(user: UserCreate, db: Session = Depends(get_db)) -> Any:
    """
    Register a new user.
    """
    try:
        logger.info(f"Registration attempt for email: {user.email}")
        
        # Check if user already exists
        db_user = db.query(User).filter(User.email == user.email).first()
        if db_user:
            logger.warning(f"User already exists with email: {user.email}")
            raise RegistrationError(
                message="Email already registered",
                context=ErrorContext(
                    source="auth.register",
                    severity=ErrorSeverity.WARNING,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={"email": user.email}
                )
            )
        
        logger.info("Creating new user...")
        try:
            # Create new user
            hashed_password = get_password_hash(user.password)
            db_user = User(
                email=user.email,
                username=user.username,
                password_hash=hashed_password,
                first_name=user.first_name,
                last_name=user.last_name
            )
            
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            logger.info(f"User created successfully with ID: {db_user.id}")
            
            # Create access token
            settings = get_settings()
            access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
            access_token = create_access_token(
                data={"sub": user.email}, expires_delta=access_token_expires
            )
            
            return {"access_token": access_token, "token_type": "Bearer"}
            
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            db.rollback()
            raise RegistrationError(
                message="Failed to create user",
                context=ErrorContext(
                    source="auth.register",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "email": user.email,
                        "error": str(e)
                    }
                )
            )
            
    except RegistrationError:
        # Re-raise known errors
        raise
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}")
        raise RegistrationError(
            message="Registration failed",
            context=ErrorContext(
                source="auth.register",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"error": str(e)}
            )
        )


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    try:
        logger.info(f"Login attempt for user: {form_data.username}")

        # Find user by email
        user = db.query(User).filter(User.email == form_data.username).first()
        if not user:
            logger.warning(f"User not found: {form_data.username}")
            raise AuthenticationError(
                message="Incorrect email or password",
                context=ErrorContext(
                    source="auth.login",
                    severity=ErrorSeverity.WARNING,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={"email": form_data.username}
                )
            )

        # Verify password
        if not verify_password(form_data.password, user.password_hash):
            logger.warning(f"Invalid password for user: {form_data.username}")
            raise AuthenticationError(
                message="Incorrect email or password",
                context=ErrorContext(
                    source="auth.login",
                    severity=ErrorSeverity.WARNING,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={"email": form_data.username}
                )
            )

        # Create access token
        access_token = create_access_token({"sub": user.email})
        logger.info(f"Login successful for user: {form_data.username}")

        return {
            "access_token": access_token,
            "token_type": "Bearer"
        }

    except AuthenticationError:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise AuthenticationError(
            message="An error occurred during login",
            context=ErrorContext(
                source="auth.login",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"error": str(e)}
            )
        )


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get current user information.
    """
    return current_user


@router.get("/check-user/{email}")
async def check_user(
    email: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    Check if a user exists (debug route).
    """
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            return {
                "exists": True,
                "email": user.email,
                "username": user.username
            }
        return {"exists": False}
        
    except Exception as e:
        logger.error(f"Error checking user existence: {str(e)}")
        raise UserValidationError(
            message="Failed to check user existence",
            context=ErrorContext(
                source="auth.check_user",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={
                    "email": email,
                    "error": str(e)
                }
            )
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(request: Request, db: Session = Depends(get_db)):
    """
    Refresh access token.
    
    Args:
        request: The request object containing the Authorization header
        db: Database session
        
    Returns:
        Token: New access token
        
    Raises:
        TokenError: If token refresh fails
        UserNotFoundError: If user not found
    """
    try:
        logger.info("Attempting to refresh token")
        
        # Get token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise TokenError(
                message="Missing or invalid Authorization header",
                error_code="AUTH-TOKEN-HDR-001",
                context=ErrorContext(
                    source="auth.refresh_token",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4())
                )
            )
        
        token = auth_header.split(" ")[1]
        
        # Verify and decode the token
        try:
            payload = verify_token(token)
            email = payload.get("sub")
            if not email:
                raise TokenError(
                    message="Invalid token: missing subject claim",
                    error_code="AUTH-TOKEN-SUB-001",
                    context=ErrorContext(
                        source="auth.refresh_token",
                        severity=ErrorSeverity.ERROR,
                        timestamp=datetime.now(UTC),
                        error_id=str(uuid4())
                    )
                )
        except TokenError as e:
            logger.warning(f"Token verification failed: {str(e)}")
            raise
            
        # Get user from database
        user = db.query(User).filter(User.email == email).first()
        if not user:
            logger.error(f"User not found during token refresh: {email}")
            raise UserNotFoundError(
                message=f"User not found: {email}",
                error_code="AUTH-USER-NFD-001",
                context=ErrorContext(
                    source="auth.refresh_token",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={"email": email}
                )
            )
            
        # Create new access token
        settings = get_settings()
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user.email},
            expires_delta=access_token_expires
        )
        
        logger.info(f"Successfully refreshed token for user: {email}")
        
        return Token(
            access_token=access_token,
            token_type="Bearer",
            user=UserResponse.model_validate(user)
        )
        
    except (TokenError, UserNotFoundError):
        # Re-raise known errors
        raise
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {str(e)}", exc_info=True)
        raise TokenError(
            message="Failed to refresh token",
            error_code="AUTH-TOKEN-ERR-001",
            context=ErrorContext(
                source="auth.refresh_token",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"error": str(e)}
            )
        )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)) -> Any:
    """
    Logout the current user.
    """
    try:
        logger.info(f"Logout successful for user: {current_user.email}")
        return {"message": "Successfully logged out"}
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise AuthenticationError(
            message="An error occurred during logout",
            context=ErrorContext(
                source="auth.logout",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"error": str(e)}
            )
        )
