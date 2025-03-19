# Users API Documentation

## Overview
The Users API (`app/api/users.py`) provides endpoints for user profile management, including profile updates, password changes, and account deletion. It implements comprehensive error handling and security measures.

## Endpoints

### Profile Management
1. **Get Profile** (`GET /me`)
   - Retrieves current user profile
   - Requires authentication
   - Returns user data
   - Handles access control

2. **Update Profile** (`PUT /me`)
   - Updates user profile data
   - Validates field updates
   - Protects sensitive fields
   - Handles validation errors

3. **Change Password** (`PUT /me/password`)
   - Updates user password
   - Validates old password
   - Secures password change
   - Handles validation

4. **Delete Account** (`DELETE /me`)
   - Deletes user account
   - Requires password confirmation
   - Handles cleanup
   - Manages dependencies

## Error Handling

### Profile Update Errors
```python
try:
    # Validate forbidden fields
    forbidden_fields = {"email", "username", "password"}
    if forbidden_fields.intersection(update_data.keys()):
        raise UserValidationError(
            message="Cannot update protected fields",
            error_code="USER-VAL-FIELD-001",
            context=ErrorContext(
                timestamp=datetime.now(UTC),
                error_id=str(uuid4()),
                user_id=str(current_user.id),
                additional_data={"forbidden_fields": list(forbidden_fields)}
            )
        )
except IntegrityError as e:
    raise UserProfileError(
        message="Failed to update profile",
        error_code="USER-PROF-UPD-001",
        context=ErrorContext(...)
    )
```

### Password Change Errors
```python
if not verify_password(password_data.old_password, current_user.password_hash):
    raise UserValidationError(
        message="Old password is incorrect",
        error_code="USER-VAL-PWD-001",
        context=ErrorContext(...)
    )
```

## Error Classes

### UserError
- **Error Code Pattern**: `USER-*`
- **Purpose**: Base class for user errors
- **Example**: `USER-GEN-001`
- **Suggestions**:
  - Check input data
  - Verify permissions
  - Review request
  - Check context

### UserValidationError
- **Error Code Pattern**: `USER-VAL-*`
- **Purpose**: Handle validation failures
- **Example**: `USER-VAL-FIELD-001`
- **Suggestions**:
  - Check field values
  - Review constraints
  - Verify format
  - Check requirements

### UserProfileError
- **Error Code Pattern**: `USER-PROF-*`
- **Purpose**: Handle profile operations
- **Example**: `USER-PROF-UPD-001`
- **Suggestions**:
  - Check data format
  - Verify changes
  - Review permissions
  - Check constraints

### UserNotFoundError
- **Error Code Pattern**: `USER-NFD-*`
- **Purpose**: Handle missing users
- **Example**: `USER-NFD-001`
- **Suggestions**:
  - Check user ID
  - Verify existence
  - Review access
  - Check deletion

## Best Practices

1. **Input Validation**
   - Validate field updates
   - Check permissions
   - Protect sensitive data
   - Sanitize inputs

2. **Error Handling**
   - Use specific errors
   - Include context
   - Log failures
   - Track changes

3. **Security**
   - Validate passwords
   - Protect fields
   - Manage sessions
   - Track changes

4. **Resource Management**
   - Handle cleanup
   - Manage sessions
   - Track resources
   - Clean invalid

## Integration Points

1. **Authentication System**
   - Token validation
   - Session management
   - Access control
   - Permission checks

2. **Database Integration**
   - Profile storage
   - Password hashing
   - Transaction management
   - Error handling

3. **Security Integration**
   - Password validation
   - Field protection
   - Access control
   - Audit logging

## Testing Requirements

1. **Endpoint Testing**
   - Profile updates
   - Password changes
   - Account deletion
   - Error handling

2. **Security Testing**
   - Field protection
   - Password security
   - Access control
   - Session management

3. **Integration Testing**
   - Database operations
   - Error handling
   - Resource cleanup
   - State management

## Future Improvements

1. **Short-term**
   - Enhanced validation
   - Better error messages
   - Field protection
   - Audit logging

2. **Long-term**
   - Profile versioning
   - Enhanced security
   - Advanced validation
   - Resource tracking 