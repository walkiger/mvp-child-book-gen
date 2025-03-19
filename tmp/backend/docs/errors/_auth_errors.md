# Authentication Error Documentation

## Overview
The authentication error module (`app/core/errors/auth.py`) provides specialized error classes for handling authentication and authorization-related errors. It extends the base error system to provide specific error handling for user authentication, authorization, token management, and session handling.

## Error Classes

### AuthError
Base class for all authentication-related errors.

```python
class AuthError(BaseError):
    def __init__(
        self,
        message: str,
        error_code: str,
        http_status_code: int = 401,
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None
    )
```

**Features**:
- Automatically prefixes error codes with "AUTH-" if not present
- Default HTTP status code 401 (Unauthorized)
- Inherits context and severity management from BaseError

### AuthenticationError
Handles user authentication failures.

```python
class AuthenticationError(AuthError):
    def __init__(
        self,
        message: str,
        error_code: str = "AUTH-CRED-INV-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    )
```

**Default Suggestions**:
- Check credentials
- Verify email and password
- Ensure account exists and is active

### AuthorizationError
Handles permission and access control failures.

```python
class AuthorizationError(AuthError):
    def __init__(
        self,
        message: str,
        required_permission: str,
        error_code: str = "AUTH-PERM-DEN-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    )
```

**Features**:
- Includes required permission in details
- Default HTTP status code 403 (Forbidden)
- Permission-specific suggestions

### TokenError
Handles JWT token-related errors.

```python
class TokenError(AuthError):
    def __init__(
        self,
        message: str,
        error_code: str = "AUTH-TOKEN-INV-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    )
```

**Features**:
- Token validation errors
- Token expiration handling
- Token refresh issues

### SessionError
Handles user session-related errors.

```python
class SessionError(AuthError):
    def __init__(
        self,
        message: str,
        error_code: str = "AUTH-SESS-INV-001",
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None
    )
```

**Features**:
- Session validation
- Session expiration
- Session management issues

## Error Codes

### Format
- `AUTH-CRED-*`: Credential-related errors
- `AUTH-PERM-*`: Permission-related errors
- `AUTH-TOKEN-*`: Token-related errors
- `AUTH-SESS-*`: Session-related errors
- `AUTH-REG-*`: Registration-related errors

### Common Codes
- `AUTH-CRED-INV-001`: Invalid credentials
- `AUTH-PERM-DEN-001`: Permission denied
- `AUTH-TOKEN-INV-001`: Invalid token
- `AUTH-TOKEN-EXP-001`: Expired token
- `AUTH-SESS-INV-001`: Invalid session
- `AUTH-REG-DUP-001`: Duplicate email registration
- `AUTH-REG-DUP-002`: Duplicate username registration
- `AUTH-REG-DB-001`: Database error during registration
- `AUTH-USER-NFD-001`: User not found

## Usage Examples

### Authentication Check
```python
try:
    user = authenticate_user(email, password)
except AuthenticationError as e:
    logger.error(f"Authentication failed: {e.message}")
    raise
```

### Permission Check
```python
if not has_permission(user, required_permission):
    raise AuthorizationError(
        message="Access denied",
        required_permission=required_permission,
        context=ErrorContext(
            timestamp=datetime.now(UTC),
            error_id=str(uuid4()),
            user_id=str(user.id)
        )
    )
```

### Token Validation
```python
try:
    payload = jwt.decode(token, secret_key, algorithms=["HS256"])
except JWTError:
    raise TokenError(
        message="Invalid token",
        context=ErrorContext(
            timestamp=datetime.now(UTC),
            error_id=str(uuid4())
        )
    )
```

## Integration

### FastAPI Integration
```python
@app.exception_handler(AuthError)
async def auth_error_handler(request: Request, error: AuthError):
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

### Middleware Usage
```python
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except AuthError as e:
        return handle_auth_error(e)
```

## Testing

### Unit Tests
```python
def test_authentication_error():
    error = AuthenticationError(
        message="Invalid credentials",
        context=ErrorContext(
            timestamp=datetime.now(UTC),
            error_id=str(uuid4())
        )
    )
    assert error.http_status_code == 401
    assert error.error_code.startswith("AUTH-CRED")

def test_authorization_error():
    error = AuthorizationError(
        message="Access denied",
        required_permission="admin",
        context=ErrorContext(
            timestamp=datetime.now(UTC),
            error_id=str(uuid4())
        )
    )
    assert error.http_status_code == 403
    assert "admin" in error.details["required_permission"]
```

## Best Practices

1. **Error Creation**
   - Use specific error classes for different scenarios
   - Include relevant context (user ID, request ID)
   - Set appropriate error codes
   - Provide helpful suggestions

2. **Security Considerations**
   - Don't expose sensitive information in errors
   - Use appropriate status codes
   - Log security-related errors
   - Include request tracking IDs

3. **Error Handling**
   - Catch and convert generic errors to auth errors
   - Preserve error context
   - Log with appropriate severity
   - Return consistent error responses

## Future Improvements

### Short-term
1. Add rate limiting for auth attempts
2. Enhance token validation
3. Improve error tracking
4. Add session management
5. Enhance security features

### Long-term
1. Add OAuth2 support
2. Implement MFA errors
3. Add biometric auth errors
4. Enhance audit logging
5. Add ML-based security 