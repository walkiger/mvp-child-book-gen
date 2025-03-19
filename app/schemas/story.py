# app/schemas/story.py

"""
Pydantic schemas for story-related data models.
"""

from datetime import datetime, UTC
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, ConfigDict, ValidationError
from app.core.errors.base import ErrorContext, ErrorSeverity
from app.core.errors.story import StoryValidationError


class AgeGroup(str, Enum):
    """Valid age groups for stories."""
    AGE_1_2 = "1-2"
    AGE_3_5 = "3-5"
    AGE_6_8 = "6-8"
    AGE_9_12 = "9-12"


class StoryTone(str, Enum):
    """Valid story tone options."""
    WHIMSICAL = "whimsical"
    EDUCATIONAL = "educational"
    ADVENTUROUS = "adventurous"
    CALMING = "calming"


class MoralLesson(str, Enum):
    """Valid moral lesson options."""
    KINDNESS = "kindness"
    COURAGE = "courage"
    FRIENDSHIP = "friendship"
    HONESTY = "honesty"
    PERSEVERANCE = "perseverance"


class StoryBase(BaseModel):
    """Base schema for story operations."""
    title: str
    age_group: str = Field(..., pattern="^(1-2|3-5|6-8|9-12)$")
    page_count: int = Field(..., ge=1, le=20)
    character_id: int
    story_tone: str = Field(..., pattern="^(whimsical|educational|adventurous|calming)$")
    moral_lesson: Optional[str] = Field(None, pattern="^(kindness|courage|friendship|honesty|perseverance)$")
    theme: Optional[str] = None
    moral: Optional[str] = None

    @field_validator("title")
    def validate_title(cls, v):
        """Validate story title."""
        if not v or not v.strip():
            error_context = ErrorContext(
                source="schemas.story.StoryBase.validate_title",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"received_value": v}
            )
            raise StoryValidationError(
                message="Story title cannot be empty",
                error_code="VAL-STORY-REQ-001",
                context=error_context
            )
        if len(v) > 100:
            error_context = ErrorContext(
                source="schemas.story.StoryBase.validate_title",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"received_value": v, "max_length": 100}
            )
            raise StoryValidationError(
                message="Story title cannot exceed 100 characters",
                error_code="VAL-STORY-LEN-001",
                context=error_context
            )
        return v

    @field_validator("age_group")
    def validate_age_group(cls, v):
        """Validate story age group."""
        if v not in [ag.value for ag in AgeGroup]:
            error_context = ErrorContext(
                source="schemas.story.StoryBase.validate_age_group",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={
                    "received_value": v,
                    "allowed_values": [ag.value for ag in AgeGroup]
                }
            )
            raise StoryValidationError(
                message=f"Invalid age group: {v}",
                error_code="VAL-STORY-FMT-001",
                context=error_context
            )
        return v

    @field_validator("story_tone")
    def validate_story_tone(cls, v):
        """Validate story tone."""
        if v not in [st.value for st in StoryTone]:
            error_context = ErrorContext(
                source="schemas.story.StoryBase.validate_story_tone",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={
                    "received_value": v,
                    "allowed_values": [st.value for st in StoryTone]
                }
            )
            raise StoryValidationError(
                message=f"Invalid story tone: {v}",
                error_code="VAL-STORY-FMT-002",
                context=error_context
            )
        return v

    @field_validator("moral_lesson")
    def validate_moral_lesson(cls, v):
        """Validate moral lesson if provided."""
        if v is not None and v not in [ml.value for ml in MoralLesson]:
            error_context = ErrorContext(
                source="schemas.story.StoryBase.validate_moral_lesson",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={
                    "received_value": v,
                    "allowed_values": [ml.value for ml in MoralLesson]
                }
            )
            raise StoryValidationError(
                message=f"Invalid moral lesson: {v}",
                error_code="VAL-STORY-FMT-003",
                context=error_context
            )
        return v


class StoryCreate(StoryBase):
    """Schema for creating a new story."""
    temperature: float = Field(
        default=1.2,
        ge=0.0,
        le=2.0,
        examples=[1.2],
        description="Controls creativity (0=strict, 2=random). Default: 1.2"
    )

    @field_validator("temperature")
    def validate_temperature(cls, v):
        """Validate temperature value."""
        if v < 0.0 or v > 2.0:
            error_context = ErrorContext(
                source="schemas.story.StoryCreate.validate_temperature",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={
                    "received_value": v,
                    "min_value": 0.0,
                    "max_value": 2.0
                }
            )
            raise StoryValidationError(
                message="Temperature must be between 0.0 and 2.0",
                error_code="VAL-STORY-FMT-004",
                context=error_context
            )
        return v


class StoryResponse(StoryBase):
    """Schema for returning story details."""
    id: int
    user_id: int
    content: Dict[str, Any]
    created_at: datetime
    character: Dict[str, Any]
    status: str

    model_config = ConfigDict(from_attributes=True)

    @field_validator("created_at", mode="before")
    def format_datetime(cls, v):
        """Convert datetime to ISO format string."""
        if isinstance(v, datetime):
            return v.replace(tzinfo=UTC) if v.tzinfo is None else v
        return v

    @field_validator("character")
    def format_character(cls, v):
        """Convert character model to dictionary."""
        if hasattr(v, "id"):
            # Convert SQLAlchemy model instance to dict
            character_dict = {
                "id": v.id,
                "name": v.name,
                "traits": v.traits,
                "image_prompt": v.image_prompt,
                "images": []
            }
            
            # Handle images if they exist
            if hasattr(v, "images") and v.images is not None:
                character_dict["images"] = [
                    {
                        "id": img.id,
                        "url": f"/api/images/{img.id}",
                        "format": img.image_format
                    }
                    for img in v.images
                ]
            
            return character_dict
        return v if isinstance(v, dict) else {}


class StoryUpdate(BaseModel):
    """Schema for updating existing stories."""
    title: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    age_group: Optional[str] = Field(None, pattern="^(1-2|3-5|6-8|9-12)$")
    page_count: Optional[int] = Field(None, ge=1, le=20)
    story_tone: Optional[str] = Field(None, pattern="^(whimsical|educational|adventurous|calming)$")
    moral_lesson: Optional[str] = Field(None, pattern="^(kindness|courage|friendship|honesty|perseverance)$")


class StoryPublic(BaseModel):
    """Public-facing story schema without sensitive data."""
    id: int
    title: str
    age_group: AgeGroup
    story_tone: StoryTone
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [{
                "id": 1,
                "title": "The Brave Little Turtle",
                "age_group": "3-5",
                "story_tone": "adventurous",
                "created_at": "2024-02-20T12:00:00"
            }]
        }
    }