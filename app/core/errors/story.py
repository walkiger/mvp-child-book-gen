"""
Story Error Handling

This module defines story-specific errors extending the base error system.
"""

from typing import Optional, Dict, Any, List

from .base import BaseError, ErrorContext, ErrorSeverity


class StoryError(BaseError):
    """Base class for all story-related errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        http_status_code: int = 500,
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None
    ):
        if not error_code.startswith('STORY-'):
            error_code = f"STORY-{error_code}"
        super().__init__(
            message,
            error_code,
            http_status_code,
            context,
            details,
            suggestions
        )


class StoryGenerationError(StoryError):
    """Story generation process failures."""
    
    def __init__(
        self,
        message: str,
        generation_step: str,
        error_code: str = "STORY-GEN-FAIL-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            'generation_step': generation_step
        })
        
        super().__init__(
            message,
            error_code,
            http_status_code=500,
            context=context,
            details=details,
            suggestions=[
                "Check story generation parameters",
                "Verify AI model availability",
                "Review content guidelines"
            ]
        )
        self.set_severity(ErrorSeverity.ERROR)


class StoryValidationError(StoryError):
    """Story content validation failures."""
    
    def __init__(
        self,
        message: str,
        content_issue: str,
        error_code: str = "STORY-VAL-FAIL-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            'content_issue': content_issue
        })
        
        super().__init__(
            message,
            error_code,
            http_status_code=422,
            context=context,
            details=details,
            suggestions=[
                "Review content guidelines",
                "Check age appropriateness",
                "Verify story structure"
            ]
        )
        self.set_severity(ErrorSeverity.WARNING)


class StoryPersistenceError(StoryError):
    """Story saving/loading failures."""
    
    def __init__(
        self,
        message: str,
        story_id: str,
        operation: str,
        error_code: str = "STORY-PERS-FAIL-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            'story_id': story_id,
            'operation': operation
        })
        
        super().__init__(
            message,
            error_code,
            http_status_code=500,
            context=context,
            details=details,
            suggestions=[
                "Check storage system availability",
                "Verify story data integrity",
                "Ensure proper file permissions"
            ]
        )
        self.set_severity(ErrorSeverity.ERROR)


class StoryRenderError(StoryError):
    """Story rendering/formatting failures."""
    
    def __init__(
        self,
        message: str,
        format_type: str,
        error_code: str = "STORY-REND-FAIL-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            'format_type': format_type
        })
        
        super().__init__(
            message,
            error_code,
            http_status_code=500,
            context=context,
            details=details,
            suggestions=[
                "Check rendering engine status",
                "Verify format compatibility",
                "Review template integrity"
            ]
        )
        self.set_severity(ErrorSeverity.ERROR)


class StoryNotFoundError(StoryError):
    """Story not found in the database."""
    
    def __init__(
        self,
        story_id: str,
        message: str = None,
        error_code: str = "STORY-NOT-FOUND-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        message = message or f"Story with ID {story_id} not found"
        details = details or {}
        details.update({
            'story_id': story_id
        })
        
        super().__init__(
            message,
            error_code,
            http_status_code=404,
            context=context,
            details=details,
            suggestions=[
                "Verify the story ID is correct",
                "Check if the story was deleted",
                "Ensure the story exists in the database"
            ]
        )
        self.set_severity(ErrorSeverity.WARNING)


class StoryCreationError(StoryError):
    """Story creation process failures."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "STORY-CREATE-FAIL-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message,
            error_code,
            http_status_code=500,
            context=context,
            details=details,
            suggestions=[
                "Check story creation parameters",
                "Verify database connection",
                "Ensure all required fields are provided"
            ]
        )
        self.set_severity(ErrorSeverity.ERROR)


class StoryUpdateError(StoryError):
    """Story update process failures."""
    
    def __init__(
        self,
        message: str,
        story_id: str,
        error_code: str = "STORY-UPDATE-FAIL-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            'story_id': story_id
        })
        
        super().__init__(
            message,
            error_code,
            http_status_code=500,
            context=context,
            details=details,
            suggestions=[
                "Verify story exists",
                "Check update parameters",
                "Ensure proper permissions"
            ]
        )
        self.set_severity(ErrorSeverity.ERROR)


class StoryDeletionError(StoryError):
    """Story deletion process failures."""
    
    def __init__(
        self,
        message: str,
        story_id: str,
        error_code: str = "STORY-DELETE-FAIL-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            'story_id': story_id
        })
        
        super().__init__(
            message,
            error_code,
            http_status_code=500,
            context=context,
            details=details,
            suggestions=[
                "Verify story exists",
                "Check deletion permissions",
                "Ensure no dependent resources"
            ]
        )
        self.set_severity(ErrorSeverity.ERROR) 