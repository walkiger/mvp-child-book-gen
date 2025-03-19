"""
API router configuration and error handling setup.
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from datetime import datetime, UTC
from uuid import uuid4
import traceback
import logging

from app.api import users, characters, auth, stories, generations, images
from app.core.errors.api import APIError, RequestValidationError, ResponseError
from app.core.errors.base import ErrorContext, ErrorSeverity

# Setup logger
logger = logging.getLogger(__name__)

# Create the main API router
api_router = APIRouter()

# Include all sub-routers
api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(users.router, prefix="/users")
api_router.include_router(characters.router, prefix="/characters")
api_router.include_router(stories.router, prefix="/stories")
api_router.include_router(generations.router, prefix="/generations")
api_router.include_router(images.router, prefix="/images")

# Exception handlers
@api_router.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    """Handle all API-related errors with detailed error context."""
    error_context = exc.error_context or ErrorContext(
        source="api",
        severity=ErrorSeverity.ERROR,
        timestamp=datetime.now(UTC),
        error_id=str(uuid4()),
        additional_data={
            "path": str(request.url),
            "method": request.method,
            "client_host": request.client.host if request.client else None,
            "error_type": exc.__class__.__name__
        }
    )
    
    # Log the error with context
    logger.error(
        f"API Error: {exc.message} | Code: {exc.error_code} | ID: {error_context.error_id}",
        extra={"error_context": error_context.dict()}
    )
    
    return JSONResponse(
        status_code=exc.http_status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "suggestions": exc.suggestions,
                "error_id": error_context.error_id,
                "timestamp": error_context.timestamp.isoformat()
            }
        }
    )

@api_router.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors with detailed error context."""
    error_context = exc.error_context or ErrorContext(
        source="api.validation",
        severity=ErrorSeverity.WARNING,
        timestamp=datetime.now(UTC),
        error_id=str(uuid4()),
        additional_data={
            "path": str(request.url),
            "method": request.method,
            "validation_errors": exc.details,
            "error_type": "RequestValidationError"
        }
    )
    
    # Log the validation error
    logger.warning(
        f"Validation Error: {exc.message} | Code: {exc.error_code} | ID: {error_context.error_id}",
        extra={"error_context": error_context.dict()}
    )
    
    return JSONResponse(
        status_code=exc.http_status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "suggestions": exc.suggestions,
                "error_id": error_context.error_id,
                "timestamp": error_context.timestamp.isoformat()
            }
        }
    )

@api_router.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors with comprehensive error context."""
    error_context = ErrorContext(
        source="api.internal",
        severity=ErrorSeverity.ERROR,
        timestamp=datetime.now(UTC),
        error_id=str(uuid4()),
        additional_data={
            "path": str(request.url),
            "method": request.method,
            "error_type": exc.__class__.__name__,
            "traceback": traceback.format_exc(),
            "client_host": request.client.host if request.client else None
        }
    )
    
    error = ResponseError(
        message="An unexpected error occurred",
        error_code="API-INTERNAL-ERR-001",
        context=error_context,
        details=str(exc),
        suggestions=["Please try again later", "Contact support if the issue persists"]
    )
    
    # Log the unexpected error
    logger.error(
        f"Unexpected Error: {str(exc)} | Code: {error.error_code} | ID: {error_context.error_id}",
        extra={"error_context": error_context.dict()},
        exc_info=True
    )
    
    return JSONResponse(
        status_code=error.http_status_code,
        content={
            "error": {
                "code": error.error_code,
                "message": error.message,
                "details": error.details,
                "suggestions": error.suggestions,
                "error_id": error_context.error_id,
                "timestamp": error_context.timestamp.isoformat()
            }
        }
    ) 