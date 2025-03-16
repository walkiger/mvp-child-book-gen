"""
Character-specific error handling classes.
"""

from typing import Optional
from fastapi import status
from app.core.error_handling import APIError

class CharacterNotFoundError(APIError):
    """Error for character not found"""
    def __init__(self, character_id: int, details: Optional[str] = None, **kwargs):
        super().__init__(
            message=f"Character with ID {character_id} not found",
            error_code="CHAR-404",
            http_status=status.HTTP_404_NOT_FOUND,
            details=details,
            **kwargs
        )

class CharacterCreationError(APIError):
    """Error for character creation failures"""
    def __init__(self, message: str, details: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            error_code="CHAR-CREATE-001",
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
            **kwargs
        )

class CharacterUpdateError(APIError):
    """Error for character update failures"""
    def __init__(self, character_id: int, details: Optional[str] = None, **kwargs):
        super().__init__(
            message=f"Failed to update character with ID {character_id}",
            error_code="CHAR-UPDATE-001",
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
            **kwargs
        )

class CharacterImageError(APIError):
    """Error for character image generation/selection failures"""
    def __init__(self, message: str, details: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            error_code="CHAR-IMG-001",
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
            **kwargs
        )

class CharacterValidationError(APIError):
    """Error for character validation failures"""
    def __init__(self, message: str, details: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            error_code="CHAR-VAL-001",
            http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
            **kwargs
        )

class CharacterDeletionError(APIError):
    """Error for character deletion failures"""
    def __init__(self, character_id: int, details: Optional[str] = None, **kwargs):
        super().__init__(
            message=f"Failed to delete character with ID {character_id}",
            error_code="CHAR-DEL-001",
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
            **kwargs
        ) 