# app/schemas/user.py

"""
Pydantic models (schemas) for user operations.
"""

from datetime import datetime, UTC
from typing import Optional
from uuid import uuid4
import re

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from app.core.errors.base import ErrorContext, ErrorSeverity
from app.core.errors.user import UserValidationError


class UserBase(BaseModel):
    """
    Base model for user with common fields.
    """
    username: str = Field(..., max_length=50)
    email: EmailStr
    first_name: str = Field(..., max_length=30)
    last_name: str = Field(..., max_length=30)
    phone_number: Optional[str] = Field(None, max_length=15)

    @field_validator("username")
    def validate_username(cls, v):
        """Validate username."""
        if not v or not v.strip():
            error_context = ErrorContext(
                source="schemas.user.UserBase.validate_username",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"received_value": v}
            )
            raise UserValidationError(
                message="Username cannot be empty",
                error_code="VAL-USER-REQ-001",
                context=error_context
            )
        if len(v) > 50:
            error_context = ErrorContext(
                source="schemas.user.UserBase.validate_username",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"received_value": v, "max_length": 50}
            )
            raise UserValidationError(
                message="Username cannot exceed 50 characters",
                error_code="VAL-USER-LEN-001",
                context=error_context
            )
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            error_context = ErrorContext(
                source="schemas.user.UserBase.validate_username",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"received_value": v, "pattern": "^[a-zA-Z0-9_-]+$"}
            )
            raise UserValidationError(
                message="Username can only contain letters, numbers, underscores, and hyphens",
                error_code="VAL-USER-FMT-001",
                context=error_context
            )
        return v

    @field_validator("first_name", "last_name")
    def validate_name(cls, v, info):
        """Validate first and last name."""
        field_name = info.field_name
        if not v or not v.strip():
            error_context = ErrorContext(
                source=f"schemas.user.UserBase.validate_{field_name}",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"received_value": v, "field": field_name}
            )
            raise UserValidationError(
                message=f"{field_name.replace('_', ' ').title()} cannot be empty",
                error_code="VAL-USER-REQ-002",
                context=error_context
            )
        if len(v) > 30:
            error_context = ErrorContext(
                source=f"schemas.user.UserBase.validate_{field_name}",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"received_value": v, "max_length": 30, "field": field_name}
            )
            raise UserValidationError(
                message=f"{field_name.replace('_', ' ').title()} cannot exceed 30 characters",
                error_code="VAL-USER-LEN-002",
                context=error_context
            )
        return v

    @field_validator("phone_number")
    def validate_phone_number(cls, v):
        """Validate phone number if provided."""
        if v is not None:
            if not re.match(r"^\+?1?\d{9,15}$", v):
                error_context = ErrorContext(
                    source="schemas.user.UserBase.validate_phone_number",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={"received_value": v, "pattern": "^\+?1?\d{9,15}$"}
                )
                raise UserValidationError(
                    message="Invalid phone number format",
                    error_code="VAL-USER-FMT-002",
                    context=error_context
                )
        return v


class UserCreate(UserBase):
    """
    Model for creating a new user.
    """
    password: str = Field(..., min_length=8)

    @field_validator("password")
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            error_context = ErrorContext(
                source="schemas.user.UserCreate.validate_password",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"received_value": "***", "min_length": 8}
            )
            raise UserValidationError(
                message="Password must be at least 8 characters long",
                error_code="VAL-USER-LEN-003",
                context=error_context
            )
        if not re.match(r"^(?=.*[A-Za-z])(?=.*\d)[\w\s@$!%*#?&+\-=/\\|:;.,~^()[\]{}\"'`<>]{8,}$", v):
            error_context = ErrorContext(
                source="schemas.user.UserCreate.validate_password",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"pattern": "At least one letter and one number"}
            )
            raise UserValidationError(
                message="Password must contain at least one letter and one number",
                error_code="VAL-USER-FMT-003",
                context=error_context
            )
        return v


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

    @field_validator("address_line1", "address_line2", "city", "state", "country")
    def validate_address_fields(cls, v, info):
        """Validate address-related fields."""
        field_name = info.field_name
        if v is not None:
            max_lengths = {
                "address_line1": 100,
                "address_line2": 100,
                "city": 50,
                "state": 50,
                "country": 50
            }
            if len(v) > max_lengths[field_name]:
                error_context = ErrorContext(
                    source=f"schemas.user.UserUpdate.validate_{field_name}",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={
                        "received_value": v,
                        "max_length": max_lengths[field_name],
                        "field": field_name
                    }
                )
                raise UserValidationError(
                    message=f"{field_name.replace('_', ' ').title()} cannot exceed {max_lengths[field_name]} characters",
                    error_code="VAL-USER-LEN-004",
                    context=error_context
                )
        return v

    @field_validator("postal_code")
    def validate_postal_code(cls, v):
        """Validate postal code if provided."""
        if v is not None:
            if len(v) > 20:
                error_context = ErrorContext(
                    source="schemas.user.UserUpdate.validate_postal_code",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={"received_value": v, "max_length": 20}
                )
                raise UserValidationError(
                    message="Postal code cannot exceed 20 characters",
                    error_code="VAL-USER-LEN-005",
                    context=error_context
                )
            if not re.match(r"^[A-Za-z0-9\s-]+$", v):
                error_context = ErrorContext(
                    source="schemas.user.UserUpdate.validate_postal_code",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={"received_value": v, "pattern": "^[A-Za-z0-9\s-]+$"}
                )
                raise UserValidationError(
                    message="Invalid postal code format",
                    error_code="VAL-USER-FMT-004",
                    context=error_context
                )
        return v


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

    model_config = ConfigDict(from_attributes=True)


class PasswordChange(BaseModel):
    """
    Model for changing the user's password.
    """
    old_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    def validate_new_password(cls, v):
        """Validate new password strength."""
        if len(v) < 8:
            error_context = ErrorContext(
                source="schemas.user.PasswordChange.validate_new_password",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"min_length": 8}
            )
            raise UserValidationError(
                message="New password must be at least 8 characters long",
                error_code="VAL-USER-LEN-006",
                context=error_context
            )
        if not re.match(r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,}$", v):
            error_context = ErrorContext(
                source="schemas.user.PasswordChange.validate_new_password",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"pattern": "At least one letter and one number"}
            )
            raise UserValidationError(
                message="New password must contain at least one letter and one number",
                error_code="VAL-USER-FMT-005",
                context=error_context
            )
        return v


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

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    """
    Model for user login request.
    """
    email: EmailStr
    password: str = Field(..., min_length=8)

    @field_validator("password")
    def validate_login_password(cls, v):
        """Validate login password."""
        if len(v) < 8:
            error_context = ErrorContext(
                source="schemas.user.LoginRequest.validate_login_password",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"min_length": 8}
            )
            raise UserValidationError(
                message="Password must be at least 8 characters long",
                error_code="VAL-USER-LEN-007",
                context=error_context
            )
        return v


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
    sub: Optional[str] = None
    is_admin: bool = False
