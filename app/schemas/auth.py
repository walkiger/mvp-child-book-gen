"""
Pydantic schemas for authentication.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, ConfigDict


class UserInfo(BaseModel):
    id: int
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    is_admin: bool = False


class Token(BaseModel):
    access_token: str
    token_type: str
    user: Optional[UserInfo] = None


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    is_admin: bool = False


class UserBase(BaseModel):
    email: EmailStr
    username: str
    first_name: str
    last_name: str


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    is_admin: bool = False

    model_config = ConfigDict(from_attributes=True) 