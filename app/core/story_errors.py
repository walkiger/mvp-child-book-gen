"""
Story-specific error handling classes.
"""

from typing import Optional
from fastapi import status
from app.core.error_handling import APIError

class StoryNotFoundError(APIError):
    """Error for story not found"""
    def __init__(self, story_id: int, details: Optional[str] = None, **kwargs):
        super().__init__(
            message=f"Story with ID {story_id} not found",
            error_code="STORY-404",
            http_status=status.HTTP_404_NOT_FOUND,
            details=details,
            **kwargs
        )

class StoryCreationError(APIError):
    """Error for story creation failures"""
    def __init__(self, message: str, details: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            error_code="STORY-CREATE-001",
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
            **kwargs
        )

class StoryUpdateError(APIError):
    """Error for story update failures"""
    def __init__(self, story_id: int, details: Optional[str] = None, **kwargs):
        super().__init__(
            message=f"Failed to update story with ID {story_id}",
            error_code="STORY-UPDATE-001",
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
            **kwargs
        )

class StoryGenerationError(APIError):
    """Error for story generation failures"""
    def __init__(self, message: str, details: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            error_code="STORY-GEN-001",
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
            **kwargs
        )

class StoryValidationError(APIError):
    """Error for story validation failures"""
    def __init__(self, message: str, details: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            error_code="STORY-VAL-001",
            http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
            **kwargs
        )

class StoryDeletionError(APIError):
    """Error for story deletion failures"""
    def __init__(self, story_id: int, details: Optional[str] = None, **kwargs):
        super().__init__(
            message=f"Failed to delete story with ID {story_id}",
            error_code="STORY-DEL-001",
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
            **kwargs
        ) 