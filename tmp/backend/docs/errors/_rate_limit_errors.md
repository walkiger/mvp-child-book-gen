# Rate Limiter Error Documentation

## Overview

The rate limiter error system provides robust handling of rate limiting scenarios, ensuring proper API usage control and preventing abuse.

## Error Types

### RateLimitError
Base class for all rate limiting errors.

```python
class RateLimitError(BaseError):
    def __init__(self, message: str, error_context: ErrorContext)
```

### RateLimitExceededError
Raised when a client exceeds their rate limit.

```python
class RateLimitExceededError(RateLimitError):
    error_code = "RATE-LIM-001"
```

#### Context Properties
- `limit_type`: Type of limit exceeded (e.g., "default", "chat", "image")
- `current_count`: Current request count
- `max_limit`: Maximum allowed requests
- `retry_after`: Seconds until limit resets

### RateLimitConfigError
Raised when there are configuration issues with rate limiting.

```python
class RateLimitConfigError(RateLimitError):
    error_code = "RATE-CFG-001"
```

## Rate Limiter Implementation

### Window-based Rate Limiting
```python
class RateLimiter:
    def check_rate_limit(
        self,
        request: Request,
        limit_type: str = "default"
    ) -> None:
        # Raises RateLimitExceededError if limit exceeded
```

### Key Generation
```python
def _get_key(
    self,
    request: Request,
    limit_type: str
) -> str:
    # Returns: "{limit_type}:{ip}:{user_id}"
```

## Error Handling Examples

### Basic Rate Limit Check
```python
try:
    limiter.check_rate_limit(request)
except RateLimitExceededError as e:
    # Access retry information
    retry_after = e.error_context.additional_data["retry_after"]
    raise HTTPException(
        status_code=429,
        detail=str(e),
        headers={"Retry-After": str(retry_after)}
    )
```

### Custom Limit Types
```python
try:
    limiter.check_rate_limit(request, limit_type="image_generation")
except RateLimitExceededError as e:
    # Handle image-specific rate limiting
    logger.warning(f"Image rate limit exceeded: {e.error_context.to_dict()}")
    raise
```

## Testing Rate Limiting

### Test Cases
1. Basic rate limit enforcement
2. Different limit types
3. Window reset behavior
4. Key generation
5. Error context validation
6. Retry-After header
7. Configuration validation

### Example Test
```python
def test_rate_limiter_check_limit_exceeded(error_context):
    limiter = RateLimiter()
    limiter.set_test_limits({"default": 2})
    
    # Make requests up to limit
    limiter.check_rate_limit(request)
    limiter.check_rate_limit(request)
    
    # Next request should fail
    with pytest.raises(RateLimitExceededError) as exc_info:
        limiter.check_rate_limit(request)
    
    error = exc_info.value
    assert error.error_code == "RATE-LIM-001"
    assert "retry_after" in error.error_context.additional_data
```

## Best Practices

### Rate Limit Configuration
1. Set appropriate limits per endpoint
2. Configure reasonable window sizes
3. Use different limit types for different operations
4. Include buffer for burst traffic

### Error Handling
1. Always include retry-after information
2. Log rate limit violations
3. Monitor rate limit patterns
4. Provide clear error messages

### Client Communication
1. Include rate limit headers
   - X-RateLimit-Limit
   - X-RateLimit-Remaining
   - X-RateLimit-Reset
2. Document rate limits in API docs
3. Provide clear error responses

## Performance Considerations

### Memory Usage
- Efficient key storage
- Regular cleanup of expired windows
- Monitoring of memory consumption

### Response Time
- Fast key generation
- Efficient limit checking
- Minimal impact on successful requests

### Scalability
- Distributed rate limiting support
- Redis backend option
- Cluster-aware configuration

## Monitoring and Alerts

### Metrics to Track
1. Rate limit violations per endpoint
2. Near-limit requests
3. Unique clients affected
4. Window reset patterns

### Alert Conditions
1. Sudden spike in violations
2. Sustained high usage
3. Unusual patterns
4. Configuration changes 