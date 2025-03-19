"""
Pydantic schemas for authentication.
"""

from typing import Optional, Dict, Any
from datetime import datetime, UTC
from uuid import uuid4
import re

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from app.core.errors.base import ErrorContext, ErrorSeverity
from app.core.errors.auth import AuthValidationError


class UserInfo(BaseModel):
    id: int
    email: EmailStr = Field(..., description="User's email address")
    username: str = Field(..., min_length=1, max_length=50)
    first_name: str = Field(..., min_length=1, max_length=30)
    last_name: str = Field(..., min_length=1, max_length=30)
    is_admin: bool = False

    @field_validator("username")
    def validate_username(cls, v):
        """Validate username."""
        if not v or not v.strip():
            error_context = ErrorContext(
                source="schemas.auth.UserInfo.validate_username",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"received_value": v}
            )
            raise AuthValidationError(
                message="Username cannot be empty",
                field="username",
                error_code="VAL-AUTH-REQ-001",
                context=error_context
            )
        if len(v) > 50:
            error_context = ErrorContext(
                source="schemas.auth.UserInfo.validate_username",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"received_value": v, "max_length": 50}
            )
            raise AuthValidationError(
                message="Username cannot exceed 50 characters",
                field="username",
                error_code="VAL-AUTH-LEN-001",
                context=error_context
            )
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            error_context = ErrorContext(
                source="schemas.auth.UserInfo.validate_username",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"received_value": v, "pattern": "^[a-zA-Z0-9_-]+$"}
            )
            raise AuthValidationError(
                message="Username can only contain letters, numbers, underscores, and hyphens",
                field="username",
                error_code="VAL-AUTH-FMT-001",
                context=error_context
            )
        return v

    @field_validator("first_name", "last_name")
    def validate_name(cls, v, info):
        """Validate first and last name."""
        field_name = info.field_name
        if not v or not v.strip():
            error_context = ErrorContext(
                source=f"schemas.auth.UserInfo.validate_{field_name}",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"received_value": v, "field": field_name}
            )
            raise AuthValidationError(
                message=f"{field_name.replace('_', ' ').title()} cannot be empty",
                field=field_name,
                error_code="VAL-AUTH-REQ-002",
                context=error_context
            )
        if len(v) > 30:
            error_context = ErrorContext(
                source=f"schemas.auth.UserInfo.validate_{field_name}",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"received_value": v, "max_length": 30, "field": field_name}
            )
            raise AuthValidationError(
                message=f"{field_name.replace('_', ' ').title()} cannot exceed 30 characters",
                field=field_name,
                error_code="VAL-AUTH-LEN-002",
                context=error_context
            )
        return v


class Token(BaseModel):
    access_token: str = Field(..., min_length=32)
    token_type: str = Field(..., pattern="^Bearer$")
    user: Optional[UserInfo] = None

    @field_validator("access_token")
    def validate_access_token(cls, v):
        """Validate access token."""
        if not v or not v.strip():
            error_context = ErrorContext(
                source="schemas.auth.Token.validate_access_token",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"received_value": "***"}
            )
            raise AuthValidationError(
                message="Access token cannot be empty",
                field="access_token",
                error_code="VAL-AUTH-REQ-003",
                context=error_context
            )
        if len(v) < 32:
            error_context = ErrorContext(
                source="schemas.auth.Token.validate_access_token",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"min_length": 32}
            )
            raise AuthValidationError(
                message="Access token must be at least 32 characters long",
                field="access_token",
                error_code="VAL-AUTH-LEN-003",
                context=error_context
            )
        return v

    @field_validator("token_type")
    def validate_token_type(cls, v):
        """Validate token type."""
        if v != "Bearer":
            error_context = ErrorContext(
                source="schemas.auth.Token.validate_token_type",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"received_value": v, "expected_value": "Bearer"}
            )
            raise AuthValidationError(
                message="Token type must be 'Bearer'",
                field="token_type",
                error_code="VAL-AUTH-FMT-002",
                context=error_context
            )
        return v


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    is_admin: bool = False

    @field_validator("sub")
    def validate_sub(cls, v):
        """Validate subject claim."""
        if v is not None and not v.strip():
            error_context = ErrorContext(
                source="schemas.auth.TokenPayload.validate_sub",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"received_value": v}
            )
            raise AuthValidationError(
                message="Subject claim cannot be empty if provided",
                field="sub",
                error_code="VAL-AUTH-FMT-003",
                context=error_context
            )
        return v


class UserBase(BaseModel):
    email: EmailStr = Field(..., description="User's email address")
    username: str = Field(..., min_length=1, max_length=50)
    first_name: str = Field(..., min_length=1, max_length=30)
    last_name: str = Field(..., min_length=1, max_length=30)

    @field_validator("username")
    def validate_username(cls, v):
        """Validate username."""
        if not v or not v.strip():
            error_context = ErrorContext(
                source="schemas.auth.UserBase.validate_username",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"received_value": v}
            )
            raise AuthValidationError(
                message="Username cannot be empty",
                field="username",
                error_code="VAL-AUTH-REQ-004",
                context=error_context
            )
        if len(v) > 50:
            error_context = ErrorContext(
                source="schemas.auth.UserBase.validate_username",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"received_value": v, "max_length": 50}
            )
            raise AuthValidationError(
                message="Username cannot exceed 50 characters",
                field="username",
                error_code="VAL-AUTH-LEN-004",
                context=error_context
            )
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            error_context = ErrorContext(
                source="schemas.auth.UserBase.validate_username",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"received_value": v, "pattern": "^[a-zA-Z0-9_-]+$"}
            )
            raise AuthValidationError(
                message="Username can only contain letters, numbers, underscores, and hyphens",
                field="username",
                error_code="VAL-AUTH-FMT-004",
                context=error_context
            )
        return v

    @field_validator("first_name", "last_name")
    def validate_name(cls, v, info):
        """Validate first and last name."""
        field_name = info.field_name
        if not v or not v.strip():
            error_context = ErrorContext(
                source=f"schemas.auth.UserBase.validate_{field_name}",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"received_value": v, "field": field_name}
            )
            raise AuthValidationError(
                message=f"{field_name.replace('_', ' ').title()} cannot be empty",
                field=field_name,
                error_code="VAL-AUTH-REQ-005",
                context=error_context
            )
        if len(v) > 30:
            error_context = ErrorContext(
                source=f"schemas.auth.UserBase.validate_{field_name}",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"received_value": v, "max_length": 30, "field": field_name}
            )
            raise AuthValidationError(
                message=f"{field_name.replace('_', ' ').title()} cannot exceed 30 characters",
                field=field_name,
                error_code="VAL-AUTH-LEN-005",
                context=error_context
            )
        return v


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

    @field_validator("password")
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            error_context = ErrorContext(
                source="schemas.auth.UserCreate.validate_password",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"min_length": 8}
            )
            raise AuthValidationError(
                message="Password must be at least 8 characters long",
                field="password",
                error_code="VAL-AUTH-LEN-006",
                context=error_context
            )
        if not re.match(r"^(?=.*[A-Za-z])(?=.*\d)[\w\s@$!%*#?&+\-=/\\|:;.,~^()[\]{}\"'`<>]{8,}$", v):
            error_context = ErrorContext(
                source="schemas.auth.UserCreate.validate_password",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"pattern": "At least one letter and one number"}
            )
            raise AuthValidationError(
                message="Password must contain at least one letter and one number",
                field="password",
                error_code="VAL-AUTH-FMT-005",
                context=error_context
            )
        return v


class UserResponse(UserBase):
    id: int
    is_admin: bool = False

    model_config = ConfigDict(from_attributes=True) 