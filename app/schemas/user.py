"""
Pydantic models (schemas) for user operations.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """
    Base model for user with common fields.
    """
    username: str = Field(..., max_length=50)
    email: EmailStr
    first_name: str = Field(..., max_length=30)
    last_name: str = Field(..., max_length=30)
    phone_number: Optional[str] = Field(None, max_length=15)


class UserCreate(UserBase):
    """
    Model for creating a new user.
    """
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """
    Model for updating user information.
    """
    first_name: Optional[str] = Field(None, max_length=30)
    last_name: Optional[str] = Field(None, max_length=30)
    phone_number: Optional[str] = Field(None, max_length=15)
    address_line1: Optional[str] = Field(None, max_length=100)
    address_line2: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=50)
    state: Optional[str] = Field(None, max_length=50)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=50)


class UserResponse(UserBase):
    """
    Model for returning user information in responses.
    """
    id: int
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True


class PasswordChange(BaseModel):
    """
    Model for changing the user's password.
    """
    old_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)


class PasswordDelete(BaseModel):
    """
    Model for confirming the user's password before account deletion.
    """
    password: str = Field(..., min_length=8)


class Message(BaseModel):
    """
    Model for returning simple messages.
    """
    detail: str


class UserPublic(BaseModel):
    """
    Model for returning public user information.
    """
    id: int
    username: str
    first_name: str
    last_name: str
    avatar_url: Optional[str] = None

    class Config:
        orm_mode = True


class LoginRequest(BaseModel):
    """
    Model for user login request.
    """
    email: EmailStr
    password: str = Field(..., min_length=8)


class Token(BaseModel):
    """
    Model for access token response.
    """
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """
    Model for storing token data.
    """
    user_id: Optional[int] = None
