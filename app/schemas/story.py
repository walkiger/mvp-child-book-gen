# app/schemas/story.py

"""
Pydantic schemas for story-related data models.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field, field_validator, ConfigDict


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
    age_group: str = Field(..., pattern="^(1-2|3-6|6-9|10-12)$")
    page_count: int = Field(..., ge=1, le=20)
    character_id: int
    story_tone: str = Field(..., pattern="^(whimsical|educational|adventurous|calming)$")
    moral_lesson: Optional[str] = Field(None, pattern="^(kindness|courage|friendship|honesty|perseverance)$")


class StoryCreate(StoryBase):
    """Schema for creating a new story."""
    temperature: float = Field(
        default=1.2,
        ge=0.0,
        le=2.0,
        examples=[1.2],
        description="Controls creativity (0=strict, 2=random). Default: 1.2"
    )


class StoryResponse(StoryBase):
    """Schema for returning story details."""
    id: int
    user_id: int
    content: Dict[str, Any]
    created_at: str
    character: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class StoryUpdate(BaseModel):
    """Schema for updating existing stories."""
    title: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    age_group: Optional[str] = Field(None, pattern="^(1-2|3-6|6-9|10-12)$")
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