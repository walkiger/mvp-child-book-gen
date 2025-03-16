"""
OpenAI client configuration and initialization.
"""

from openai import AsyncOpenAI
from app.config import settings


def get_openai_client() -> AsyncOpenAI:
    """
    Get an initialized OpenAI client instance.
    
    Returns:
        AsyncOpenAI client instance
    """
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY) 