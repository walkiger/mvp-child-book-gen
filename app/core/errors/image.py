"""
Image Error Handling

This module defines image-specific errors extending the base error system.
"""

from typing import Optional, Dict, Any, List

from .base import BaseError, ErrorContext, ErrorSeverity


class ImageError(BaseError):
    """Base class for all image-related errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        http_status_code: int = 500,
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None
    ):
        if not error_code.startswith('IMG-'):
            error_code = f"IMG-{error_code}"
        super().__init__(
            message,
            error_code,
            http_status_code,
            context,
            details,
            suggestions
        )


class ImageGenerationError(ImageError):
    """Image generation process failures."""
    
    def __init__(
        self,
        message: str,
        generation_step: str,
        error_code: str = "IMG-GEN-FAIL-001",
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
                "Check image generation parameters",
                "Verify AI model status",
                "Review prompt guidelines"
            ]
        )
        self.set_severity(ErrorSeverity.ERROR)


class ImageProcessingError(ImageError):
    """Image processing and manipulation failures."""
    
    def __init__(
        self,
        message: str,
        operation: str,
        image_format: str,
        error_code: str = "IMG-PROC-FAIL-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            'operation': operation,
            'image_format': image_format
        })
        
        super().__init__(
            message,
            error_code,
            http_status_code=500,
            context=context,
            details=details,
            suggestions=[
                "Check image format compatibility",
                "Verify processing parameters",
                "Review operation requirements"
            ]
        )
        self.set_severity(ErrorSeverity.ERROR)


class ImageStorageError(ImageError):
    """Image storage and retrieval failures."""
    
    def __init__(
        self,
        message: str,
        storage_operation: str,
        image_id: str,
        error_code: str = "IMG-STOR-FAIL-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            'storage_operation': storage_operation,
            'image_id': image_id
        })
        
        super().__init__(
            message,
            error_code,
            http_status_code=500,
            context=context,
            details=details,
            suggestions=[
                "Check storage system availability",
                "Verify file permissions",
                "Ensure sufficient storage space"
            ]
        )
        self.set_severity(ErrorSeverity.ERROR)


class ImageValidationError(ImageError):
    """Image validation and content safety failures."""
    
    def __init__(
        self,
        message: str,
        validation_type: str,
        issue: str,
        error_code: str = "IMG-VAL-FAIL-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            'validation_type': validation_type,
            'issue': issue
        })
        
        super().__init__(
            message,
            error_code,
            http_status_code=422,
            context=context,
            details=details,
            suggestions=[
                "Check content safety guidelines",
                "Verify image dimensions",
                "Review file size limits"
            ]
        )
        self.set_severity(ErrorSeverity.WARNING) 