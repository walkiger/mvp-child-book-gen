# app/main.py

"""
Main FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter

from app.api.auth import router as auth_router
from app.api.characters import router as characters_router
from app.api.stories import router as stories_router
from app.api.images import router as images_router
from app.api.monitoring import router as monitoring_router
from app.database.seed import init_db
from app.core.rate_limiter import check_rate_limit
from app.config import settings
from app.database.migrations import create_migration_script, run_migrations
from utils.error_handling import register_exception_handlers, DatabaseError, setup_logger
import os

# Set up logger
logger = setup_logger("app", "logs/app.log")

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
            raise DatabaseError("Failed to run database migrations", details=str(e))
    
    # Initialize the database
    try:
        init_db()  # This is a synchronous function, not async
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise DatabaseError("Failed to initialize database", details=str(e))
    
    yield
    # Cleanup resources if needed
    logger.info("Application shutting down")

# Create FastAPI app
app = FastAPI(
    title="MVP Child Book Generator API",
    description="API for generating children's books",
    version="1.0.0",
    lifespan=lifespan,
)

# Register exception handlers
register_exception_handlers(app)

# Configure CORS - MUST be before any routes
logger.info(f"Configuring CORS with allowed origins: {settings.ALLOWED_ORIGINS}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Mount routers directly on the app with full paths
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(characters_router, prefix="/api/characters", tags=["characters"])
app.include_router(stories_router, prefix="/api/stories", tags=["stories"])
app.include_router(images_router, prefix="/api/images", tags=["images"])
# Add the monitoring router
app.include_router(monitoring_router, tags=["monitoring"])

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """
    Rate limiting middleware.
    """
    # Skip rate limiting for non-API routes
    if not request.url.path.startswith("/api/"):
        return await call_next(request)
    
    # Check rate limit
    allowed, message = await check_rate_limit(request)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={"detail": message}
        )
    
    # Continue processing the request
    response = await call_next(request)
    return response

@app.get("/")
def read_root():
    """
    Root endpoint.
    """
    return {
        "message": "Welcome to the MVP Child Book Generator API",
        "docs": "/docs",
    }
