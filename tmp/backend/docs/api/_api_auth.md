# Authentication API Documentation

## Overview
The Authentication API (`app/api/auth.py`) provides endpoints for user registration, authentication, and session management. It implements OAuth2 with JWT tokens for secure authentication.

## Endpoints

### Authentication
1. **Register** (`POST /register`)
   - Creates new user account
   - Validates user data
   - Hashes password
   - Returns access token

2. **Login** (`POST /login`)
   - OAuth2 compatible login
   - Validates credentials
   - Issues access token
   - Handles authentication

3. **Get Current User** (`GET /me`)
   - Returns user profile
   - Requires authentication
   - Validates token
   - Returns user data

4. **Check User** (`GET /check-user/{email}`)
   - Checks user existence
   - Debug endpoint
   - Email validation
   - Returns status

## Error Handling

### Registration Errors
```python
@router.post("/register", response_model=Token, status_code=201)
async def register(user: UserCreate, db: Session = Depends(get_db)) -> Any:
    try:
        # Check if user exists
        db_user = db.query(User).filter(User.email == user.email).first()
        if db_user:
            raise RegistrationError(
                message="Email already registered",
                details=f"A user with email {user.email} already exists"
            )
        
        # Create new user
        try:
            hashed_password = get_password_hash(user.password)
            db_user = User(
                email=user.email,
                username=user.username,
                password_hash=hashed_password,
                first_name=user.first_name,
                last_name=user.last_name
            )
            db.add(db_user)
            db.commit()
            
        except Exception as e:
            db.rollback()
            raise RegistrationError(
                message="Failed to create user",
                details=str(e)
            )
            
    except RegistrationError:
        raise
    except Exception as e:
        raise RegistrationError(
            message="Registration failed",
            details=str(e)
        )
```

### Authentication Errors
```python
@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    try:
        # Find user
        user = db.query(User).filter(User.email == form_data.username).first()
        if not user:
            raise AuthenticationError("Incorrect email or password")

        # Verify password
        if not verify_password(form_data.password, user.password_hash):
            raise AuthenticationError("Incorrect email or password")

    except AuthenticationError as e:
        raise
    except Exception as e:
        raise AuthenticationError("An error occurred during login")
```

## Error Classes

### AuthenticationError
- **Error Code Pattern**: `AUTH-*`
- **Purpose**: Handle login failures
- **Example**: `AUTH-LOGIN-001`
- **Suggestions**:
  - Check credentials
  - Verify email
  - Check password
  - Try password reset

### RegistrationError
- **Error Code Pattern**: `AUTH-REG-*`
- **Purpose**: Handle registration issues
- **Example**: `AUTH-REG-001`
- **Suggestions**:
  - Check email format
  - Verify uniqueness
  - Validate password
  - Check required fields

### TokenError
- **Error Code Pattern**: `AUTH-TKN-*`
- **Purpose**: Handle token issues
- **Example**: `AUTH-TKN-001`
- **Suggestions**:
  - Check token validity
  - Verify expiration
  - Check signature
  - Try re-login

### PermissionError
- **Error Code Pattern**: `AUTH-PRM-*`
- **Purpose**: Handle access issues
- **Example**: `AUTH-PRM-001`
- **Suggestions**:
  - Check permissions
  - Verify role
  - Review access
  - Request access

## Best Practices

1. **Input Validation**
   - Validate email format
   - Check password strength
   - Verify required fields
   - Sanitize inputs

2. **Error Handling**
   - Use specific errors
   - Include context
   - Log attempts
   - Track failures

3. **Security**
   - Hash passwords
   - Secure tokens
   - Rate limit
   - Monitor attempts

4. **Session Management**
   - Track sessions
   - Handle expiration
   - Manage refresh
   - Clean invalid

## Integration Points

1. **Database Integration**
   - User storage
   - Session tracking
   - Error logging
   - Audit trail

2. **Token Management**
   - JWT creation
   - Token validation
   - Refresh handling
   - Revocation

3. **Security Integration**
   - Password hashing
   - Rate limiting
   - IP blocking
   - Audit logging

## Testing Requirements

1. **Endpoint Testing**
   - Registration flow
   - Login process
   - Token validation
   - Error handling

2. **Security Testing**
   - Password security
   - Token security
   - Access control
   - Rate limiting

3. **Integration Testing**
   - Database operations
   - Token management
   - Error recovery
   - Session handling

## Future Improvements

1. **Short-term**
   - Enhanced validation
   - Better error messages
   - Rate limiting
   - Session tracking

2. **Long-term**
   - OAuth providers
   - MFA support
   - Password reset
   - Session management 