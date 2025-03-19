# Rate Limiter Documentation

## Overview
The Rate Limiter module (`rate_limiter.py`) provides rate limiting functionality for API endpoints, with robust error handling, configurable limits, and support for different types of rate limiting.

## Core Components

### 1. Rate Limiter Class
```python
class RateLimiter:
    """Rate limiter implementation using a simple in-memory store."""
    
    def __init__(self):
        """Initialize rate limiter with default limits."""
```

Key features:
- In-memory rate limiting store
- Configurable limits per endpoint type
- Support for test configurations
- Automatic window management

### 2. Rate Limit Types
Default rate limits:
- Chat: 5 requests/minute
- Image: 3 requests/minute
- Token: 20000 tokens/minute
- Default: 60 requests/minute

### 3. Window Management
```python
def _get_window_start(self, now: float) -> float:
    """Get the start of the current minute window."""
```

Features:
- Minute-based windows
- Automatic window expiration
- Request counting per window
- Window reset on expiration

## Error Handling

### Error Classes

1. **QuotaExceededError**
   - Purpose: Rate limit quota exceeded
   - Usage: When request count exceeds limit
   - Example:
   ```python
   raise QuotaExceededError(
       message=f"Rate limit exceeded for {limit_type}",
       limit_type=limit_type,
       current_usage=window["count"],
       limit=limit,
       reset_time=reset_time,
       context=context,
       details={
           "retry_after": retry_after,
           "window_start": window["start"],
           "window_end": window["start"] + 60
       }
   )
   ```

2. **ConcurrencyLimitError**
   - Purpose: Concurrent requests limit
   - Usage: When too many simultaneous requests
   - Example:
   ```python
   raise ConcurrencyLimitError(
       message="Too many concurrent requests",
       max_concurrent=max_concurrent,
       current_concurrent=current_concurrent,
       context=context
   )
   ```

3. **BurstLimitError**
   - Purpose: Request burst protection
   - Usage: When requests come too quickly
   - Example:
   ```python
   raise BurstLimitError(
       message="Request burst limit exceeded",
       burst_limit=burst_limit,
       current_burst=current_burst,
       window_seconds=window_seconds,
       context=context
   )
   ```

4. **CostLimitError**
   - Purpose: Cost-based rate limiting
   - Usage: When cost threshold exceeded
   - Example:
   ```python
   raise CostLimitError(
       message="Cost limit exceeded",
       cost_limit=cost_limit,
       current_cost=current_cost,
       reset_time=reset_time,
       context=context
   )
   ```

### Error Patterns

1. **Rate Limit Check**
   ```python
   try:
       rate_limiter.check_rate_limit(request, "image")
   except QuotaExceededError as e:
       # Handle rate limit exceeded
       logger.warning(f"Rate limit exceeded: {e}")
       raise
   ```

2. **Remaining Requests**
   ```python
   remaining = rate_limiter.get_remaining(request, "chat")
   if remaining < 2:
       logger.warning("Rate limit approaching")
   ```

## Best Practices

### Rate Limit Management
1. Use appropriate limit types
2. Monitor remaining requests
3. Handle rate limit errors
4. Implement backoff strategies
5. Log rate limit events

### Resource Management
1. Clear expired windows
2. Monitor memory usage
3. Handle concurrent access
4. Implement cleanup routines
5. Track usage patterns

### Error Handling
1. Use specific error types
2. Include context information
3. Provide retry guidance
4. Log limit violations
5. Monitor error patterns

## Integration Points

### FastAPI Integration
- Request middleware
- Error handlers
- Response headers
- State management

### Monitoring Integration
- Usage tracking
- Error reporting
- Performance metrics
- Resource monitoring

### Configuration Integration
- Settings management
- Limit configuration
- Test configurations
- Environment handling

## Testing Requirements

### Functional Testing
1. Test rate limit enforcement
2. Verify window management
3. Check error handling
4. Test limit types
5. Verify remaining counts

### Performance Testing
1. Test concurrent access
2. Measure memory usage
3. Check window cleanup
4. Test burst handling
5. Verify scalability

### Integration Testing
1. Test with FastAPI
2. Verify error handling
3. Check header management
4. Test configuration
5. Verify monitoring

## Future Improvements

### Short-term
1. Add distributed storage
2. Implement token bucket
3. Add request prioritization
4. Enhance monitoring
5. Improve cleanup

### Long-term
1. Add dynamic limits
2. Implement fair queuing
3. Add rate prediction
4. Enhance scalability
5. Add analytics

## Common Utilities

### Request Identification
```python
def _get_key(self, request: Request, limit_type: str) -> str:
    """Generate a unique key for the request."""
```

### Window Management
```python
def _get_window_start(self, now: float) -> float:
    """Get the start of the current minute window."""
```

### Limit Configuration
```python
@property
def limits(self) -> Dict[str, int]:
    """Get rate limits from settings or test configuration."""
``` 