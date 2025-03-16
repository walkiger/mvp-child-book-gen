"""
Pydantic schemas for character-related data models.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class CharacterBase(BaseModel):
    name: str
    traits: List[str] = []


class CharacterCreate(CharacterBase):
    dalle_version: Optional[str] = "dall-e-3"


class CharacterUpdate(CharacterBase):
    name: Optional[str] = None
    traits: Optional[List[str]] = None
    image_prompt: Optional[str] = None


class CharacterResponse(CharacterBase):
    id: int
    user_id: int
    image_path: Optional[str] = None
    generated_images: Optional[List[str]] = None
    image_prompt: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CharacterImageGenerationProgress(BaseModel):
    """Schema for character image generation progress updates."""
    progress: int = Field(..., description="Progress percentage (0-100)")
    image_url: Optional[str] = Field(None, description="URL of the generated image when complete")
    message: Optional[str] = Field(None, description="Status message")


class PromptEnhanceRequest(BaseModel):
    """Schema for prompt enhancement requests."""
    name: str = Field(..., description="Character name")
    traits: List[str] = Field(..., description="Character traits")
    base_prompt: str = Field(..., description="Base prompt to enhance") 