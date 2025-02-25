from datetime import datetime, timedelta
from fastapi import HTTPException, status

# Global counters (use Redis in production)
openai_request_count = 0
openai_token_count = 0
last_reset_time = datetime.utcnow()

def check_rate_limits():
    global openai_request_count, openai_token_count, last_reset_time

    # Reset counters every minute
    if (datetime.utcnow() - last_reset_time) > timedelta(minutes=1):
        openai_request_count = 0
        openai_token_count = 0
        last_reset_time = datetime.utcnow()

    # Enforce global limits
    if openai_request_count >= 5 or openai_token_count >= 20000:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again in 1 minute.",
            headers={"Retry-After": "60"}
        )

def update_rate_metrics(tokens_used: int):
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
