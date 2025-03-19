# app/main.py

"""
Main FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import uuid
import os
from datetime import datetime, UTC
from uuid import uuid4

from app.api import auth, stories, characters, images
from app.api.monitoring import router as monitoring_router
from app.database.seed import init_db
from app.core.rate_limiter import rate_limiter
from app.config import get_settings, Settings
from app.database.migrations import create_migration_script, run_migrations
from app.core.errors.base import ErrorContext, ErrorSeverity
from app.core.errors.database import DatabaseError
from app.core.errors.api import APIError, InternalServerError
from app.core.errors.middleware import setup_error_handling
from app.core.logging import setup_logger
from app.core.rate_limiting import RateLimitMiddleware
from app.core.auth import get_current_user
from app.version import __version__

# Set up logger
if get_settings() is None:
    # In test mode, use default settings
    logger = setup_logger("app", "logs/app.log", level=logging.DEBUG)
else:
    # Convert string level to logging level
    log_level = getattr(logging, get_settings().log_level.upper(), logging.INFO)
    logger = setup_logger("app", "logs/app.log", level=log_level)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler to perform startup and shutdown tasks.
    """
    # Run database migrations on startup
    if os.environ.get("RUN_MIGRATIONS", "true").lower() == "true":
        try:
            logger.info("Running database migrations...")
            run_migrations()
            logger.info("Database migrations completed successfully")
        except Exception as e:
            logger.error(f"Error running migrations: {str(e)}")
            error_context = ErrorContext(
                source="main.lifespan",
                severity=ErrorSeverity.CRITICAL,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"error": str(e)}
            )
            raise DatabaseError(
                message="Failed to run database migrations",
                error_code="DB-MIG-001",
                context=error_context
            )
    
    # Initialize the database
    try:
        init_db()  # This is a synchronous function, not async
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        error_context = ErrorContext(
            source="main.lifespan",
            severity=ErrorSeverity.CRITICAL,
            timestamp=datetime.now(UTC),
            error_id=str(uuid4()),
            additional_data={"error": str(e)}
        )
        raise DatabaseError(
            message="Failed to initialize database",
            error_code="DB-INIT-001",
            context=error_context
        )
    
    yield
    # Cleanup resources if needed
    logger.info("Application shutting down")

# Create FastAPI app
app = FastAPI(
    title="Child Book Generator API",
    description="API for generating personalized children's books",
    version=__version__,
    lifespan=lifespan,
    debug=True if get_settings() is None else os.environ.get("DEBUG_MODE", "false").lower() == "true"
)

# Register API error handlers
setup_error_handling(app, debug=app.debug)

# Configure CORS - MUST be before any routes
if get_settings() is None:
    # In test mode, use default settings
    allowed_origins = ["http://localhost:3000", "http://localhost:5173", "http://localhost:3001"]
    logger.info(f"Configuring CORS with default allowed origins: {allowed_origins}")
else:
    allowed_origins = get_settings().allowed_origins_list
    logger.info(f"Configuring CORS with allowed origins: {get_settings().allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "X-Requested-With",
        "X-API-Version",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
        "Retry-After"
    ],
    expose_headers=[
        "X-API-Version",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
        "Retry-After"
    ]
)

# Set up rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Add middleware for API version header
class APIVersionHeaderMiddleware(BaseHTTPMiddleware):
    """Middleware to add API version header to responses."""
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-API-Version"] = __version__
        return response

app.add_middleware(APIVersionHeaderMiddleware)

# Mount routers directly on the app with full paths
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(characters.router, prefix="/api/characters", tags=["characters"])
app.include_router(stories.router, prefix="/api/stories", tags=["stories"])
app.include_router(images.router, prefix="/api/images", tags=["images"])
# Add the monitoring router with v1 prefix for health check
app.include_router(monitoring_router, prefix="/api/v1/monitoring", tags=["monitoring"])

@app.get("/")
def read_root():
    """Root endpoint that returns basic API information."""
    return {
        "message": "Welcome to the Child Book Generator API"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": __version__}
