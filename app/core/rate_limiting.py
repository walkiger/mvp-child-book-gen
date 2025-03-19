"""
Rate limiting middleware for FastAPI.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.core.rate_limiter import rate_limiter
from app.core.errors.rate_limit import QuotaExceededError
import logging

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limits on API endpoints."""
    
    async def dispatch(self, request: Request, call_next):
        """
        Process the request and enforce rate limits.
        
        Args:
            request: The incoming request
            call_next: The next middleware/endpoint in the chain
            
        Returns:
            Response from the next middleware/endpoint
        """
        try:
            # Determine if this is an OpenAI API call
            path = request.url.path.lower()
            
            # Skip rate limiting for non-API endpoints
            if not path.startswith("/api/"):
                return await call_next(request)
                
            # Determine the rate limit type based on the endpoint
            limit_type = "default"
            
            # Check for OpenAI API calls
            if path.startswith("/api/stories/generate"):
                limit_type = "openai_chat"
            elif path.startswith("/api/images/generate"):
                limit_type = "openai_image"
            elif path.startswith("/api/characters") and request.method == "POST":
                # Character creation uses both chat and image APIs
                # The endpoint itself will handle the specific checks
                return await call_next(request)
            
            # Check rate limit
            rate_limiter.check_rate_limit(request, limit_type)
            
            # Process the request
            response = await call_next(request)
            
            # Add rate limit headers from request state if they exist
            if hasattr(request.state, "rate_limit_headers"):
                for header, value in request.state.rate_limit_headers.items():
                    response.headers[header] = value
                    
            return response
            
        except QuotaExceededError as e:
            # Return rate limit error response
            headers = getattr(request.state, "rate_limit_headers", {})
            return JSONResponse(
                status_code=429,
                content={
                    "message": str(e),
                    "error_code": e.error_code,
                    "details": e.details
                },
                headers=headers
            )
        except Exception as e:
            logger.error(f"Error in rate limit middleware: {str(e)}")
            return await call_next(request) 