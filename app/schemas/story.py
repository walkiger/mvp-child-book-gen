# app/schemas/story.py

"""
Pydantic schemas for story operations.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator


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
    title: str = Field(
        ...,
        min_length=2,
        max_length=100,
        examples=["The Brave Little Turtle"],
        description="Title of the story"
    )
    character_id: int = Field(
        ...,
        gt=0,
        examples=[1],
        description="ID of the character to use in the story"
    )
    age_group: AgeGroup = Field(
        ...,
        examples=[AgeGroup.AGE_3_5],
        description="Target age group for the story"
    )
    locations: List[str] = Field(
        ...,
        min_length=1,
        examples=[["Enchanted Forest", "Crystal Cave"]],
        description="List of locations for the story"
    )
    moral_lesson: Optional[MoralLesson] = Field(
        None,
        examples=[MoralLesson.COURAGE],
        description="Optional moral lesson for the story"
    )
    story_tone: StoryTone = Field(
        default=StoryTone.WHIMSICAL,
        examples=[StoryTone.ADVENTUROUS],
        description="Desired tone for the story"
    )

    @field_validator("locations")
    @classmethod
    def validate_locations(cls, v: List[str]) -> List[str]:
        """Validate at least one location with non-empty strings."""
        if not v:
            raise ValueError("At least one location required")
        if any(len(loc.strip()) == 0 for loc in v):
            raise ValueError("Location strings cannot be empty")
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


class StoryResponse(StoryBase):
    """Schema for returning story details."""
    id: int
    user_id: int
    content: dict = Field(
        ...,
        examples=[{"pages": ["Once upon a time..."]}],
        description="Generated story content in structured format"
    )
    created_at: datetime
    images: List[str] = Field(
        default_factory=list,
        examples=["images/story1/page1.jpg"],
        description="List of generated image paths"
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [{
                "id": 1,
                "user_id": 1,
                "title": "The Brave Little Turtle",
                "character_id": 1,
                "age_group": "3-5",
                "locations": ["Enchanted Forest"],
                "moral_lesson": "courage",
                "story_tone": "adventurous",
                "content": {"pages": ["Once upon a time..."]},
                "created_at": "2024-02-20T12:00:00",
                "images": []
            }]
        }
    }


class StoryUpdate(BaseModel):
    """Schema for updating existing stories."""
    title: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        examples=["Updated Story Title"],
        description="New title for the story"
    )
    story_tone: Optional[StoryTone] = Field(
        None,
        examples=[StoryTone.EDUCATIONAL],
        description="Updated story tone"
    )


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