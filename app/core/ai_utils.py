from datetime import datetime, timedelta, UTC
from .errors.rate_limit import QuotaExceededError
from .errors.base import ErrorContext, ErrorSeverity

# Global counters (use Redis in production)
openai_request_count = 0
openai_token_count = 0
last_reset_time = datetime.now(UTC)

def check_rate_limits():
    """
    Check OpenAI API rate limits.
    
    Raises:
        QuotaExceededError: When rate limits are exceeded
    """
    global openai_request_count, openai_token_count, last_reset_time

    # Reset counters every minute
    if (datetime.now(UTC) - last_reset_time) > timedelta(minutes=1):
        openai_request_count = 0
        openai_token_count = 0
        last_reset_time = datetime.now(UTC)

    # Enforce global limits
    if openai_request_count >= 5 or openai_token_count >= 20000:
        reset_time = last_reset_time + timedelta(minutes=1)
        context = ErrorContext(
            source="ai_utils.check_rate_limits",
            severity=ErrorSeverity.WARNING
        )
        
        if openai_request_count >= 5:
            raise QuotaExceededError(
                message="OpenAI request rate limit exceeded",
                limit_type="requests",
                current_usage=openai_request_count,
                limit=5,
                reset_time=reset_time,
                context=context
            )
        else:
            raise QuotaExceededError(
                message="OpenAI token rate limit exceeded",
                limit_type="tokens",
                current_usage=openai_token_count,
                limit=20000,
                reset_time=reset_time,
                context=context
            )

def update_rate_metrics(tokens_used: int):
    """
    Update rate limiting metrics.
    
    Args:
        tokens_used: Number of tokens used in the request
    """
    global openai_request_count, openai_token_count
    openai_request_count += 1
    openai_token_count += tokens_used


DEVELOPER_PROMPT = """
You are a professional children's book author. Follow these rules:
1. Language: Simple sentences, age-appropriate vocabulary.
2. Themes: Positive, uplifting, no conflict/scares.
3. Structure: Clear beginning-middle-end.
4. For ages 1-5: Use repetition (e.g., "Again, the bunny hopped!").
5. For ages 6-12: Add mild challenges resolved through kindness.
6. Always include vivid imagery (e.g., "sparkling scales", "giggle-filled meadows").
7. Never use markdown or special formatting.
"""
