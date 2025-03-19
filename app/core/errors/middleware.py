"""
Error Handling Middleware

This module provides middleware for handling errors in FastAPI applications.
"""

import traceback
from typing import Callable, Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .base import BaseError, ErrorContext, ErrorSeverity


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for handling all application errors."""
    
    def __init__(
        self,
        app: FastAPI,
        debug: bool = False
    ):
        super().__init__(app)
        self.debug = debug
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> JSONResponse:
        """Process the request and handle any errors."""
        try:
            return await call_next(request)
            
        except BaseError as e:
            # Our custom errors are already formatted properly
            return self._create_error_response(e)
            
        except Exception as e:
            # Wrap unknown errors in a base error
            error = BaseError(
                message=str(e),
                error_code="SYS-ERR-UNK-001",
                http_status_code=500,
                context=ErrorContext(
                    severity=ErrorSeverity.CRITICAL,
                    endpoint=str(request.url),
                    method=request.method,
                    stack_trace=traceback.format_exc() if self.debug else None
                )
            )
            return self._create_error_response(error)
    
    def _create_error_response(self, error: BaseError) -> JSONResponse:
        """Create a standardized error response."""
        response_data = {
            'success': False,
            'error': error.to_dict()
        }
        
        # In debug mode, include stack trace
        if self.debug and error.context.stack_trace:
            response_data['error']['stack_trace'] = error.context.stack_trace
        
        return JSONResponse(
            status_code=error.http_status_code,
            content=response_data
        )


def setup_error_handling(app: FastAPI, debug: bool = False) -> None:
    """Configure error handling for a FastAPI application."""
    
    # Add middleware
    app.add_middleware(ErrorHandlingMiddleware, debug=debug)
    
    # Register exception handlers
    @app.exception_handler(BaseError)
    async def handle_base_error(
        request: Request,
        error: BaseError
    ) -> JSONResponse:
        """Handle our custom errors."""
        return JSONResponse(
            status_code=error.http_status_code,
            content={'success': False, 'error': error.to_dict()}
        )
    
    @app.exception_handler(Exception)
    async def handle_unhandled_error(
        request: Request,
        error: Exception
    ) -> JSONResponse:
        """Handle any unhandled errors."""
        base_error = BaseError(
            message="An unexpected error occurred",
            error_code="SYS-ERR-UNK-001",
            http_status_code=500,
            context=ErrorContext(
                severity=ErrorSeverity.CRITICAL,
                endpoint=str(request.url),
                method=request.method,
                stack_trace=traceback.format_exc() if debug else None
            )
        )
        return JSONResponse(
            status_code=500,
            content={'success': False, 'error': base_error.to_dict()}
        ) 