# Base Error Handling System

## Overview

The base error handling system provides a unified approach to error management across the application. It centers around the `ErrorContext` class and standardized error types.

## Core Components

### ErrorContext

```python
class ErrorContext:
    def __init__(
        source: str,
        operation: str,
        error_code: str,
        severity: ErrorSeverity,
        additional_data: Optional[Dict[str, Any]] = None,
        parent_context: Optional['ErrorContext'] = None
    )
```

#### Properties
- `source`: Error origin (e.g., "database", "api")
- `operation`: Operation that failed
- `error_code`: Standardized error code
- `severity`: Error severity level
- `timestamp`: UTC timestamp of error
- `additional_data`: Context-specific data
- `parent_context`: Optional parent error context

#### Features
- Immutable after creation
- JSON serializable
- Supports error chaining
- Includes timing information
- Validates error codes and sources

### Error Severity Levels

```python
class ErrorSeverity(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
```

### Base Error Types

1. `BaseError`
   - Foundation for all custom errors
   - Includes ErrorContext support
   - Standardized formatting

2. `ValidationError`
   - Input validation failures
   - Schema validation errors

3. `DatabaseError`
   - Database operation failures
   - Connection issues
   - Integrity constraints

4. `APIError`
   - API request/response errors
   - External service failures

5. `ProcessError`
   - Process management issues
   - System operation failures

6. `RetryableError`
   - Temporary failures
   - Can be retried

## Error Handling Decorators

### @with_api_error_handling
```python
@with_api_error_handling
async def api_endpoint():
    # Handles API-specific errors
```

### @with_db_error_handling
```python
@with_db_error_handling
def database_operation():
    # Handles database-specific errors
```

### @with_validation_error_handling
```python
@with_validation_error_handling
def validate_input():
    # Handles validation-specific errors
```

### @with_retry
```python
@with_retry(max_retries=3, delay=0.1)
def retryable_operation():
    # Automatically retries on failure
```

## Error Context Usage

### Creating Error Context
```python
context = ErrorContext(
    source="api.users",
    operation="create_user",
    error_code="USER-CREATE-001",
    severity=ErrorSeverity.ERROR,
    additional_data={"user_id": 123}
)
```

### Raising Errors
```python
raise APIError(
    "Failed to create user",
    error_context=context
)
```

### Error Chaining
```python
try:
    # Operation that may fail
except ValidationError as e:
    new_context = ErrorContext(
        source="api.validation",
        operation="validate_user",
        error_code="VAL-USER-001",
        severity=ErrorSeverity.ERROR,
        parent_context=e.error_context
    )
    raise ValidationError("Invalid user data", error_context=new_context) from e
```

## Best Practices

1. **Error Context Creation**
   - Always provide meaningful source and operation
   - Use standardized error codes
   - Include relevant additional data
   - Set appropriate severity level

2. **Error Handling**
   - Use appropriate error types
   - Include error context
   - Chain errors when appropriate
   - Log errors with context

3. **Error Recovery**
   - Implement retry mechanisms for transient failures
   - Provide clear error messages
   - Include recovery instructions in error context

4. **Testing**
   - Test error scenarios
   - Verify error context data
   - Check error chaining
   - Test retry mechanisms

## Performance Considerations

1. **Error Context Creation**
   - Lightweight object creation
   - Minimal memory footprint
   - Efficient serialization

2. **Error Handling**
   - Fast error type checking
   - Efficient error chaining
   - Optimized logging

3. **Monitoring**
   - Error rate tracking
   - Performance impact measurement
   - Resource usage monitoring

## Error Code Structure

### Format
- `[DOMAIN]-[CATEGORY]-[TYPE]-[NUMBER]`
- Example: `AUTH-CRED-INV-001`

### Components
1. **Domain**: System area (AUTH, DB, API, etc.)
2. **Category**: Functional category (CRED, QUERY, PERM, etc.)
3. **Type**: Error type (INV, FAIL, DENY, etc.)
4. **Number**: Sequential identifier (001, 002, etc.)

## Usage Examples

### Basic Error Creation
```python
error = BaseError(
    message="Operation failed",
    error_code="SYS-OP-FAIL-001",
    context=ErrorContext(
        timestamp=datetime.now(UTC),
        error_id=str(uuid4())
    )
)
```

### With Full Context
```python
error = BaseError(
    message="Resource not found",
    error_code="API-RES-NFD-001",
    http_status_code=404,
    context=ErrorContext(
        timestamp=datetime.now(UTC),
        error_id=str(uuid4()),
        user_id="user123",
        request_id="req456",
        additional_data={"resource_id": "res789"}
    ),
    severity=ErrorSeverity.ERROR,
    details={"resource_type": "user"},
    suggestions=[
        "Check resource ID",
        "Verify resource exists",
        "Ensure proper access permissions"
    ]
)
```

## Integration

### Exception Handler
```python
@app.exception_handler(BaseError)
async def base_error_handler(request: Request, error: BaseError):
    return JSONResponse(
        status_code=error.http_status_code,
        content={
            "error": {
                "code": error.error_code,
                "message": error.message,
                "details": error.details,
                "suggestions": error.suggestions
            }
        }
    )
```

### Logging Integration
```python
def log_error(error: BaseError):
    log_data = {
        "error_code": error.error_code,
        "message": error.message,
        "severity": error.severity,
        "context": asdict(error.context) if error.context else None
    }
    logger.error(json.dumps(log_data))
```

## Testing

### Unit Tests
```python
def test_base_error():
    error = BaseError(
        message="Test error",
        error_code="TEST-ERR-001",
        context=ErrorContext(
            timestamp=datetime.now(UTC),
            error_id=str(uuid4())
        )
    )
    assert error.http_status_code == 500
    assert error.severity == ErrorSeverity.ERROR
    assert error.error_code == "TEST-ERR-001"

def test_error_context():
    context = ErrorContext(
        timestamp=datetime.now(UTC),
        error_id=str(uuid4()),
        user_id="test_user",
        additional_data={"test": "data"}
    )
    assert context.user_id == "test_user"
    assert "test" in context.additional_data
```

## Future Improvements

### Short-term
1. Add error aggregation
2. Enhance context collection
3. Improve error tracking
4. Add performance impact
5. Enhance testing tools

### Long-term
1. Add error analytics
2. Implement ML detection
3. Add predictive handling
4. Enhance visualization
5. Add automated resolution 