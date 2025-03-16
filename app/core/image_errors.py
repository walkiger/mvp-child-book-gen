"""
Image-specific error handling classes.
"""

from typing import Optional
from fastapi import status
from app.core.error_handling import APIError

class ImageNotFoundError(APIError):
    """Error for image not found"""
    def __init__(self, image_id: int, details: Optional[str] = None, **kwargs):
        super().__init__(
            message=f"Image with ID {image_id} not found",
            error_code="IMG-404",
            http_status=status.HTTP_404_NOT_FOUND,
            details=details,
            **kwargs
        )

class ImageFormatError(APIError):
    """Error for invalid image format"""
    def __init__(self, message: str, details: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            error_code="IMG-FMT-001",
            http_status=status.HTTP_400_BAD_REQUEST,
            details=details,
            **kwargs
        )

class ImageProcessingError(APIError):
    """Error for image processing failures"""
    def __init__(self, message: str, details: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            error_code="IMG-PROC-001",
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
            **kwargs
        )

class ImageStorageError(APIError):
    """Error for image storage failures"""
    def __init__(self, message: str, details: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            error_code="IMG-STORE-001",
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
            **kwargs
        )

class ImageValidationError(APIError):
    """Error for image validation failures"""
    def __init__(self, message: str, details: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            error_code="IMG-VAL-001",
            http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
            **kwargs
        ) 