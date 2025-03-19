"""
OpenAI client configuration and initialization.
"""

from datetime import datetime, UTC
from uuid import uuid4
import logging
from openai import AsyncOpenAI
from app.config import get_settings
from app.core.errors.base import ErrorContext, ErrorSeverity
from app.core.errors.ai import AIClientError

logger = logging.getLogger(__name__)

def get_openai_client() -> AsyncOpenAI:
    """
    Get an initialized OpenAI client instance.
    
    Returns:
        AsyncOpenAI client instance
        
    Raises:
        AIClientError: If client initialization fails
    """
    try:
        settings = get_settings()
        if not settings.openai_api_key:
            raise AIClientError(
                message="OpenAI API key not configured",
                error_code="AI-CLIENT-001",
                context=ErrorContext(
                    source="openai_client.get_openai_client",
                    severity=ErrorSeverity.ERROR,
                    timestamp=datetime.now(UTC),
                    error_id=str(uuid4())
                )
            )
        return AsyncOpenAI(api_key=settings.openai_api_key)
    except Exception as e:
        raise AIClientError(
            message="Failed to initialize OpenAI client",
            error_code="AI-CLIENT-002",
            context=ErrorContext(
                source="openai_client.get_openai_client",
                severity=ErrorSeverity.ERROR,
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                additional_data={"error": str(e)}
            )
        ) from e 