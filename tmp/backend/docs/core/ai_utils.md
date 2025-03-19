# AI Utilities Documentation

## Overview
The AI Utilities module provides core functionality for managing AI service interactions, including rate limiting, token tracking, and prompt management for the children's book generation system.

## Components

### Rate Limiting
The module implements rate limiting for OpenAI API calls:

```python
def check_rate_limits():
    """
    Check OpenAI API rate limits.
    
    Raises:
        QuotaExceededError: When rate limits are exceeded
    """
```

Key features:
- Per-minute request counting
- Token usage tracking
- Automatic counter reset
- Structured error handling

### Rate Metrics
Utilities for tracking API usage:

```python
def update_rate_metrics(tokens_used: int):
    """
    Update rate limiting metrics.
    
    Args:
        tokens_used: Number of tokens used in the request
    """
```

### Prompt Management
Predefined prompts for consistent AI interactions:
```python
DEVELOPER_PROMPT = """
You are a professional children's book author...
"""
```

## Error Handling

### Error Classes
The module uses structured error handling from the rate limiting system:

1. **QuotaExceededError**
   - Thrown when rate limits are exceeded
   - Includes detailed context and suggestions
   - Provides reset timing information

Example:
```python
try:
    check_rate_limits()
except QuotaExceededError as e:
    # Error includes:
    # - Current usage stats
    # - Limit information
    # - Reset timing
    # - Suggestions for handling
    handle_rate_limit_error(e)
```

### Error Patterns
Rate limit checking follows this pattern:
1. Check current usage
2. Compare against limits
3. Raise appropriate error with context
4. Include recovery suggestions

## Best Practices

1. **Rate Limiting**
   - Always check limits before API calls
   - Handle errors gracefully
   - Implement backoff strategies
   - Monitor usage patterns

2. **Token Management**
   - Track token usage accurately
   - Update metrics promptly
   - Monitor for anomalies
   - Implement alerts

3. **Error Handling**
   - Use structured errors
   - Include context
   - Provide suggestions
   - Log appropriately

## Integration Points
- OpenAI API Client
- Rate Limiting System
- Error Handler
- Logging System

## Testing Requirements

1. **Rate Limit Testing**
   - Test limit enforcement
   - Verify counter reset
   - Check error handling
   - Test recovery

2. **Token Tracking**
   - Test counter accuracy
   - Verify reset timing
   - Check overflow handling
   - Test concurrent updates

3. **Integration Testing**
   - Test with API client
   - Verify error propagation
   - Check metric updates
   - Test recovery flows

## Future Improvements

1. **Short-term**
   - Redis integration for counters
   - Enhanced monitoring
   - Better error tracking
   - Rate limit configuration

2. **Long-term**
   - Distributed rate limiting
   - Advanced quota management
   - ML-based rate prediction
   - Dynamic limits 