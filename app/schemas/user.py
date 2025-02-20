from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """
    Base model for user with common fields.
    """
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    phone_number: Optional[str] = None


class UserCreate(UserBase):
    """
    Model for creating a new user.
    """
    password: str


class UserUpdate(BaseModel):
    """
    Model for updating user information.
    """
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None


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
    old_password: str
    new_password: str


class PasswordDelete(BaseModel):
    """
    Model for confirming the user's password before account deletion.
    """
    password: str


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
