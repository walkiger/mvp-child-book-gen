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