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

router = APIRouter(tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


@router.post("/register", response_model=Token)
async def register(user: UserCreate, db: Session = Depends(get_db)) -> Any:
    """
    Register a new user.
    """
    print(f"Registration attempt for email: {user.email}")
    
    # Check if user already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        print(f"User already exists with email: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    print("Creating new user...")
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        password_hash=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        print(f"User created successfully with ID: {db_user.id}")
    except Exception as e:
        print(f"Error creating user: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.email}, expires_delta=access_token_expires
    )
    print("Access token created")
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get access token for valid credentials.
    """
    print(f"Login attempt for username: {form_data.username}")
    
    # Find user by email
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user:
        print(f"User not found with email: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(form_data.password, user.password_hash):
        print(f"Invalid password for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Include is_admin status in the token data
    token_data = {
        "sub": user.email,
        "is_admin": getattr(user, "is_admin", False)
    }
    
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )
    
    print(f"Login successful for user: {user.email}")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_admin": getattr(user, "is_admin", False)
        }
    }


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
    user = db.query(User).filter(User.email == email).first()
    if user:
        return {
            "exists": True,
            "email": user.email,
            "username": user.username
        }
    return {"exists": False}
