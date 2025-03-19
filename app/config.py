# app/config.py

"""
Configuration settings for the application using Pydantic's BaseSettings.

This module provides configuration settings for the application using Pydantic's BaseSettings.
"""

import logging
import os
from datetime import datetime, UTC
from typing import List, Optional
from uuid import uuid4 as uuid
import secrets

from pydantic import Field, validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

from app.core.errors.base import ErrorContext, ErrorSeverity, ConfigurationError

# Configure logging
logger = logging.getLogger(__name__)

# Load .env file explicitly
load_dotenv()

# Debug: Print all environment variables
logger.debug("Environment variables:")
for key, value in os.environ.items():
    if "key" in key.lower():
        masked_value = value[:10] + "..." if value else None
        logger.debug(f"{key}: {masked_value}")

class Settings(BaseSettings):
    """Application settings."""
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,  # Allow case-insensitive env vars
        env_prefix="",  # No prefix for env vars
        extra="allow"  # Allow extra fields
    )

    # OpenAI settings
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key",
        validation_alias="OPENAI_API_KEY"  # Explicitly set the env var name
    )

    # API settings
    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=30, gt=0)

    # Database settings
    database_name: str = "app.db"
    database_dir: str = ""

    # CORS settings
    allowed_origins: str = "http://localhost:3000"  # Default to frontend dev server

    # Upload settings
    upload_dir: str = "./uploads"
    max_upload_size: int = Field(default=5 * 1024 * 1024, gt=0)  # 5MB

    # Rate limiting
    chat_rate_limit_per_minute: int = Field(default=5, gt=0)
    image_rate_limit_per_minute: int = Field(default=3, gt=0)
    token_limit_per_minute: int = Field(default=20000, gt=0)

    # OpenAI settings
    dalle_default_version: str = Field(default="dall-e-3", pattern="^dall-e-[23]$")

    # Logging
    log_level: str = Field(
        default="DEBUG",
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"
    )

    # Testing mode
    testing: bool = False

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        """Get the database URL."""
        db_path = os.path.join(self.database_dir, self.database_name)
        return f"sqlite:///{db_path}"

    @validator("database_dir", pre=True)
    def validate_database_dir(cls, v: str) -> str:
        """Validate and create database directory if it doesn't exist."""
        if not v:
            v = os.path.join(os.getcwd(), "data")
        os.makedirs(v, exist_ok=True)
        return v

    @property
    def allowed_origins_list(self) -> List[str]:
        """Get list of allowed origins."""
        if not self.allowed_origins:
            return []
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    def validate_settings(self, force: bool = False) -> None:
        """Validate settings and create necessary directories.

        Args:
            force: If True, validate settings even in testing mode.
        """
        if not force and self.testing:
            return

        try:
            # Validate secret key
            if not self.secret_key or len(self.secret_key) < 16:
                error_context = ErrorContext(
                    source="config.Settings.validate_settings",
                    severity=ErrorSeverity.CRITICAL,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid()),
                    additional_data={"secret_key_length": len(self.secret_key) if self.secret_key else 0}
                )
                raise ConfigurationError(
                    message="SECRET_KEY is missing or too short (minimum 16 characters)",
                    error_code="CFG-SEC-001",
                    context=error_context
                )

            # Validate OpenAI API key if provided
            if self.openai_api_key and not (self.openai_api_key.startswith("sk-") or self.openai_api_key.startswith("sk-proj-")):
                error_context = ErrorContext(
                    source="config.Settings.validate_settings",
                    severity=ErrorSeverity.CRITICAL,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid()),
                    additional_data={"has_key": bool(self.openai_api_key)}
                )
                raise ConfigurationError(
                    message="OPENAI_API_KEY is invalid (must start with 'sk-' or 'sk-proj-')",
                    error_code="CFG-API-001",
                    context=error_context
                )

            # Validate allowed origins
            if self.allowed_origins:
                for origin in self.allowed_origins_list:
                    if not origin.startswith(("http://", "https://")):
                        error_context = ErrorContext(
                            source="config.Settings.validate_settings",
                            severity=ErrorSeverity.ERROR,
                            timestamp=datetime.now(UTC),
                            error_id=str(uuid()),
                            additional_data={"invalid_origin": origin}
                        )
                        raise ConfigurationError(
                            message=f"Invalid origin format: {origin}. Must start with http:// or https://",
                            error_code="CFG-CORS-001",
                            context=error_context
                        )

            # Create upload directory if it doesn't exist
            try:
                os.makedirs(self.upload_dir, exist_ok=True)
            except OSError as e:
                error_context = ErrorContext(
                    source="config.Settings.validate_settings",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid()),
                    additional_data={"upload_dir": self.upload_dir, "error": str(e)}
                )
                raise ConfigurationError(
                    message=f"Failed to create upload directory: {str(e)}",
                    error_code="CFG-DIR-001",
                    context=error_context
                )

            # Create database directory if it doesn't exist
            database_dir = os.path.dirname(self.database_path)
            try:
                os.makedirs(database_dir, exist_ok=True)
            except OSError as e:
                error_context = ErrorContext(
                    source="config.Settings.validate_settings",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid()),
                    additional_data={"database_dir": database_dir, "error": str(e)}
                )
                raise ConfigurationError(
                    message=f"Failed to create database directory: {str(e)}",
                    error_code="CFG-DIR-002",
                    context=error_context
                )

        except ConfigurationError:
            raise
        except Exception as e:
            error_context = ErrorContext(
                source="config.Settings.validate_settings",
                severity=ErrorSeverity.CRITICAL,
                timestamp=datetime.now(UTC),
                error_id=str(uuid()),
                additional_data={"error": str(e)}
            )
            raise ConfigurationError(
                message=f"Unexpected error during settings validation: {str(e)}",
                error_code="CFG-GEN-001",
                context=error_context
            )

    def __init__(self, **kwargs):
        """Initialize settings with environment variables."""
        super().__init__(**kwargs)
        
        # Don't validate settings in testing mode unless forced
        if not self.testing:
            self.validate_settings()

    @property
    def database_path(self) -> str:
        """Get the full database path."""
        if self.database_dir:
            return os.path.join(self.database_dir, self.database_name)
        return self.database_name

    @validator("upload_dir", pre=True)
    def validate_upload_dir(cls, v: str) -> str:
        """Validate and create upload directory if it doesn't exist."""
        if not os.path.exists(v):
            try:
                os.makedirs(v, exist_ok=True)
                logger.info(f"Created upload directory: {v}")
            except OSError as e:
                error_context = ErrorContext(
                    source="config.Settings",
                    severity=ErrorSeverity.ERROR,
                    additional_data={"path": v}
                )
                raise ConfigurationError(
                    f"Failed to create upload directory: {e}",
                    "CONFIG-UPLOAD-DIR-001",
                    context=error_context
                )
        
        return v

    @validator("secret_key", pre=True)
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key."""
        if not v or v == "default_secret_key":
            v = secrets.token_urlsafe(32)
            logger.warning("Using generated secret key. Consider setting a fixed key in production.")
        return v

    @validator("openai_api_key", pre=True)
    def validate_openai_api_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate OpenAI API key."""
        logger.info(f"Validating OpenAI API key. Raw value type: {type(v)}")
        if not v:
            logger.warning("OpenAI API key not set. Some features will be unavailable.")
            return None
        logger.info(f"OpenAI API key found with length: {len(v)}")
        if not (v.startswith("sk-") or v.startswith("sk-proj-")):
            logger.warning(f"Invalid OpenAI API key format. Key starts with: {v[:5]}...")
        return v

# Global settings instance
_settings = None

def get_settings() -> Settings:
    """Get application settings singleton."""
    global _settings
    if _settings is None:
        try:
            _settings = Settings()
        except Exception as e:
            error_context = ErrorContext(
                source="config.get_settings",
                severity=ErrorSeverity.CRITICAL,
                error_id=str(uuid()),
                additional_data={"error": str(e)}
            )
            raise ConfigurationError(
                message="Failed to load application settings",
                error_code="CONFIG-LOAD-001",
                context=error_context
            ) from e
    return _settings
