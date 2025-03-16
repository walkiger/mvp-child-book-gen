# app/api/auth.py

"""
Authentication API endpoints.
"""

from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.core.auth import (
    get_current_user,
    create_access_token,
    verify_password,
    get_password_hash
)
from app.database.models import User
from app.database.session import get_db
from app.schemas.auth import Token, UserCreate, UserResponse
from app.config import settings
from app.core.auth_errors import (
    AuthenticationError,
    RegistrationError,
    TokenError,
    PermissionError,
    UserNotFoundError,
    UserValidationError
)
from app.core.error_handling import setup_logger

# Set up logger
logger = setup_logger("auth", "logs/auth.log")

router = APIRouter(tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


@router.post("/register", response_model=Token)
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
                details=f"A user with email {user.email} already exists"
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
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user.email}, expires_delta=access_token_expires
            )
            
            return {"access_token": access_token, "token_type": "bearer"}
            
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            db.rollback()
            raise RegistrationError(
                message="Failed to create user",
                details=str(e)
            )
            
    except RegistrationError:
        # Re-raise known errors
        raise
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}")
        raise RegistrationError(
            message="Failed to register user",
            details=str(e)
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
                details="User not found"
            )
        
        # Verify password
        if not verify_password(form_data.password, user.password_hash):
            logger.warning(f"Invalid password for user: {form_data.username}")
            raise AuthenticationError(
                message="Incorrect email or password",
                details="Invalid password"
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        logger.info(f"Login successful for user: {form_data.username}")
        return {"access_token": access_token, "token_type": "bearer"}
        
    except AuthenticationError:
        # Re-raise known errors
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        raise AuthenticationError(
            message="Login failed",
            details=str(e)
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
            details=str(e)
        )
