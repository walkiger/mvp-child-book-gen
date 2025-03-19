"""
Pydantic schemas for character-related data models.
"""

from typing import List, Optional
from datetime import datetime, UTC
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.core.errors.base import ErrorContext, ErrorSeverity
from app.core.errors.character import CharacterValidationError


class CharacterBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    traits: List[str] = []

    @field_validator("name")
    def validate_name(cls, v):
        """Validate character name."""
        if not v or not v.strip():
            error_context = ErrorContext(
                source="schemas.character.CharacterBase.validate_name",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"received_value": v}
            )
            raise CharacterValidationError(
                message="Character name cannot be empty",
                error_code="VAL-CHAR-REQ-001",
                context=error_context
            )
        if len(v) > 50:
            error_context = ErrorContext(
                source="schemas.character.CharacterBase.validate_name",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"received_value": v, "max_length": 50}
            )
            raise CharacterValidationError(
                message="Character name cannot exceed 50 characters",
                error_code="VAL-CHAR-LEN-001",
                context=error_context
            )
        return v

    @field_validator("traits")
    def validate_traits(cls, v):
        """Validate character traits."""
        if not isinstance(v, list):
            error_context = ErrorContext(
                source="schemas.character.CharacterBase.validate_traits",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"received_value": v}
            )
            raise CharacterValidationError(
                message="Traits must be a list",
                error_code="VAL-CHAR-FMT-001",
                context=error_context
            )
        for trait in v:
            if not isinstance(trait, str) or not trait.strip():
                error_context = ErrorContext(
                    source="schemas.character.CharacterBase.validate_traits",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={"received_value": trait}
                )
                raise CharacterValidationError(
                    message="Each trait must be a non-empty string",
                    error_code="VAL-CHAR-FMT-002",
                    context=error_context
                )
            if len(trait) > 100:
                error_context = ErrorContext(
                    source="schemas.character.CharacterBase.validate_traits",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={"received_value": trait, "max_length": 100}
                )
                raise CharacterValidationError(
                    message="Each trait cannot exceed 100 characters",
                    error_code="VAL-CHAR-LEN-002",
                    context=error_context
                )
        return v


class CharacterCreate(CharacterBase):
    dalle_version: Optional[str] = "dall-e-3"

    @field_validator("dalle_version")
    def validate_dalle_version(cls, v):
        """Validate DALL-E version."""
        valid_versions = ["dall-e-2", "dall-e-3"]
        if v not in valid_versions:
            error_context = ErrorContext(
                source="schemas.character.CharacterCreate.validate_dalle_version",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={
                    "received_value": v,
                    "allowed_values": valid_versions
                }
            )
            raise CharacterValidationError(
                message=f"Invalid DALL-E version. Must be one of: {', '.join(valid_versions)}",
                error_code="VAL-CHAR-FMT-003",
                context=error_context
            )
        return v


class CharacterUpdate(CharacterBase):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    traits: Optional[List[str]] = None
    image_prompt: Optional[str] = Field(None, max_length=1000)
    image_path: Optional[str] = None
    generated_images: Optional[List[str]] = None

    @field_validator("image_prompt")
    def validate_image_prompt(cls, v):
        """Validate image prompt if provided."""
        if v is not None:
            if not v.strip():
                error_context = ErrorContext(
                    source="schemas.character.CharacterUpdate.validate_image_prompt",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={"received_value": v}
                )
                raise CharacterValidationError(
                    message="Image prompt cannot be empty if provided",
                    error_code="VAL-CHAR-FMT-004",
                    context=error_context
                )
            if len(v) > 1000:
                error_context = ErrorContext(
                    source="schemas.character.CharacterUpdate.validate_image_prompt",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={"received_value": v, "max_length": 1000}
                )
                raise CharacterValidationError(
                    message="Image prompt cannot exceed 1000 characters",
                    error_code="VAL-CHAR-LEN-003",
                    context=error_context
                )
        return v


class CharacterResponse(CharacterBase):
    id: int
    user_id: int
    image_path: Optional[str] = None
    generated_images: Optional[List[str]] = None
    image_prompt: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CharacterImageGenerationProgress(BaseModel):
    """Schema for character image generation progress updates."""
    progress: int = Field(..., description="Progress percentage (0-100)", ge=0, le=100)
    image_url: Optional[str] = Field(None, description="URL of the generated image when complete")
    message: Optional[str] = Field(None, description="Status message")

    @field_validator("progress")
    def validate_progress(cls, v):
        """Validate progress percentage."""
        if v < 0 or v > 100:
            error_context = ErrorContext(
                source="schemas.character.CharacterImageGenerationProgress.validate_progress",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={
                    "received_value": v,
                    "min_value": 0,
                    "max_value": 100
                }
            )
            raise CharacterValidationError(
                message="Progress must be between 0 and 100",
                error_code="VAL-CHAR-FMT-005",
                context=error_context
            )
        return v


class PromptEnhanceRequest(BaseModel):
    """Schema for prompt enhancement requests."""
    name: str = Field(..., description="Character name", min_length=1, max_length=50)
    traits: List[str] = Field(..., description="Character traits")
    base_prompt: str = Field(..., description="Base prompt to enhance", min_length=1, max_length=1000)

    @field_validator("base_prompt")
    def validate_base_prompt(cls, v):
        """Validate base prompt."""
        if not v.strip():
            error_context = ErrorContext(
                source="schemas.character.PromptEnhanceRequest.validate_base_prompt",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"received_value": v}
            )
            raise CharacterValidationError(
                message="Base prompt cannot be empty",
                error_code="VAL-CHAR-REQ-002",
                context=error_context
            )
        if len(v) > 1000:
            error_context = ErrorContext(
                source="schemas.character.PromptEnhanceRequest.validate_base_prompt",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"received_value": v, "max_length": 1000}
            )
            raise CharacterValidationError(
                message="Base prompt cannot exceed 1000 characters",
                error_code="VAL-CHAR-LEN-004",
                context=error_context
            )
        return v


class CharacterRefineRequest(BaseModel):
    """Schema for character refinement requests."""
    traits: List[str] = Field(..., description="Updated character traits")
    style_preferences: Optional[str] = Field(None, description="Optional style preferences for image generation", max_length=500)

    @field_validator("style_preferences")
    def validate_style_preferences(cls, v):
        """Validate style preferences if provided."""
        if v is not None:
            if len(v) > 500:
                error_context = ErrorContext(
                    source="schemas.character.CharacterRefineRequest.validate_style_preferences",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4()),
                    additional_data={"received_value": v, "max_length": 500}
                )
                raise CharacterValidationError(
                    message="Style preferences cannot exceed 500 characters",
                    error_code="VAL-CHAR-LEN-005",
                    context=error_context
                )
        return v 