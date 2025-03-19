"""
Character-specific error handling classes.
"""

from datetime import datetime, UTC
from typing import Optional, Dict, Any
from uuid import uuid4

from app.core.errors.base import BaseError, ErrorContext, ErrorSeverity

class CharacterError(BaseError):
    """Base error class for character-related errors."""
    def __init__(
        self,
        message: str,
        error_code: str,
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if not context:
            context = ErrorContext(
                source="character",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data=details
            )
        super().__init__(message=message, error_code=error_code, context=context)

class CharacterNotFoundError(CharacterError):
    """Error raised when a character is not found."""
    def __init__(
        self,
        character_id: str,
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"Character not found: {character_id}"
        error_code = "CHAR-404"
        if not context:
            context = ErrorContext(
                source="character.not_found",
                severity=ErrorSeverity.WARNING,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"character_id": character_id, **(details or {})}
            )
        super().__init__(message=message, error_code=error_code, context=context)

class CharacterCreationError(CharacterError):
    """Error raised when character creation fails."""
    def __init__(
        self,
        message: str = "Failed to create character",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_code = "CHAR-500"
        if not context:
            context = ErrorContext(
                source="character.creation",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data=details
            )
        super().__init__(message=message, error_code=error_code, context=context)

class CharacterUpdateError(CharacterError):
    """Error raised when character update fails."""
    def __init__(
        self,
        character_id: int,
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"Failed to update character with ID {character_id}"
        error_code = "CHAR-UPDATE-001"
        if not context:
            context = ErrorContext(
                source="character.update",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"character_id": character_id, **(details or {})}
            )
        super().__init__(message=message, error_code=error_code, context=context)

class CharacterImageError(CharacterError):
    """Error raised when character image generation/selection fails."""
    def __init__(
        self,
        message: str,
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_code = "CHAR-IMG-001"
        if not context:
            context = ErrorContext(
                source="character.image",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data=details
            )
        super().__init__(message=message, error_code=error_code, context=context)

class CharacterValidationError(CharacterError):
    """Error raised when character data validation fails."""
    def __init__(
        self,
        message: str = "Invalid character data",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_code = "CHAR-VAL-001"
        if not context:
            context = ErrorContext(
                source="character.validation",
                severity=ErrorSeverity.WARNING,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data=details
            )
        super().__init__(message=message, error_code=error_code, context=context)

class CharacterDeletionError(CharacterError):
    """Error raised when character deletion fails."""
    def __init__(
        self,
        character_id: int,
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"Failed to delete character with ID {character_id}"
        error_code = "CHAR-DEL-001"
        if not context:
            context = ErrorContext(
                source="character.deletion",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"character_id": character_id, **(details or {})}
            )
        super().__init__(message=message, error_code=error_code, context=context) 