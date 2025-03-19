# Base API Documentation

## Overview
The Base API (`app/api/api.py`) provides the core API router configuration and global error handling setup. It integrates all sub-routers and implements consistent error handling across the application.

## Router Structure

### Main Components
1. **API Router**
   - Central routing configuration
   - Sub-router integration
   - Error handler registration
   - Global middleware

2. **Sub-routers**
   - Authentication (`/auth`)
   - Users (`/users`)
   - Characters (`/characters`)
   - Stories (`/stories`)
   - Generations (`/generations`)
   - Images (`/images`)

## Error Handling

### Global Error Handler
```python
@api_router.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    """Handle all API-related errors."""
    return JSONResponse(
        status_code=exc.http_status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "suggestions": exc.suggestions
            }
        }
    )
```

### Validation Error Handler
```python
@api_router.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    return JSONResponse(
        status_code=exc.http_status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "suggestions": exc.suggestions
            }
        }
    )
```

### General Exception Handler
```python
@api_router.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    error = ResponseError(
        message="An unexpected error occurred",
        error_code="API-INTERNAL-ERR-001",
        context=ErrorContext(
            timestamp=datetime.now(UTC),
            error_id=str(uuid4()),
            additional_data={"error": str(exc)}
        )
    )
    return JSONResponse(...)
```

## Error Classes

### APIError
- **Error Code Pattern**: `API-*`
- **Purpose**: Base class for API errors
- **Example**: `API-GEN-001`
- **Suggestions**:
  - Check request
  - Verify input
  - Review logs
  - Check context

### RequestValidationError
- **Error Code Pattern**: `API-VAL-*`
- **Purpose**: Handle request validation
- **Example**: `API-VAL-001`
- **Suggestions**:
  - Check input format
  - Verify required fields
  - Review constraints
  - Check types

### ResponseError
- **Error Code Pattern**: `API-RES-*`
- **Purpose**: Handle response errors
- **Example**: `API-RES-001`
- **Suggestions**:
  - Check processing
  - Verify output
  - Review format
  - Check handling

## Best Practices

1. **Router Configuration**
   - Consistent prefixes
   - Clear organization
   - Proper tagging
   - Version management

2. **Error Handling**
   - Consistent format
   - Detailed messages
   - Helpful suggestions
   - Context inclusion

3. **Response Format**
   - Standard structure
   - Clear status codes
   - Detailed errors
   - Useful metadata

4. **Security**
   - Request validation
   - Error sanitization
   - Access control
   - Audit logging

## Integration Points

1. **Sub-routers**
   - Route integration
   - Error propagation
   - Middleware chain
   - Context sharing

2. **Error System**
   - Error handling
   - Context tracking
   - Logging integration
   - Metrics collection

3. **Middleware**
   - Request tracking
   - Authentication
   - Rate limiting
   - Logging

## Testing Requirements

1. **Router Testing**
   - Route integration
   - Prefix handling
   - Error propagation
   - Middleware chain

2. **Error Testing**
   - Error handling
   - Status codes
   - Response format
   - Context tracking

3. **Integration Testing**
   - Sub-router integration
   - Error propagation
   - Middleware chain
   - State management

## Future Improvements

1. **Short-term**
   - Enhanced validation
   - Better error messages
   - Request tracking
   - Performance monitoring

2. **Long-term**
   - API versioning
   - Rate limiting
   - Caching layer
   - Advanced routing 