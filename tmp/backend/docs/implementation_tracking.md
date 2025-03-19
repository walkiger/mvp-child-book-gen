# Error Handling Implementation Tracking

## Overview
This document tracks the implementation status of standardized error handling across the codebase.

## Implementation Status

### Core Layer
| File | Status | Last Updated | Notes |
|------|--------|--------------|-------|
| image_generation.py | ✅ Complete | Mar 18, 2024 | Standardized error handling with ErrorContext |
| story_generation.py | ✅ Complete | Mar 18, 2024 | Proper error handling with context |
| ai_utils.py | ✅ Complete | Mar 18, 2024 | Rate limiting with ErrorContext |
| config.py | ✅ Complete | Mar 18, 2024 | Configuration error handling |
| main.py | ✅ Complete | Mar 18, 2024 | Global error handling middleware |
| seed.py | ✅ Complete | Mar 18, 2024 | Database seeding error handling |
| rate_limiter.py | ✅ Complete | Mar 18, 2024 | Rate limiting error handling with QuotaExceededError |
| rate_limiting.py | ✅ Complete | Mar 18, 2024 | Rate limiting middleware with ErrorContext |
| openai_client.py | ✅ Complete | Mar 18, 2024 | OpenAI client error handling with AIClientError |
| db_utils.py | ✅ Complete | Mar 18, 2024 | Database utilities error handling |
| security.py | ✅ Complete | Mar 18, 2024 | Security utilities error handling |
| auth.py | ✅ Complete | Mar 18, 2024 | Authentication error handling |

### API Layer
| File | Status | Last Updated | Notes |
|------|--------|--------------|-------|
| api.py | ✅ Complete | Mar 18, 2024 | Global API error handling with standardized error classes |
| monitoring.py | ✅ Complete | Mar 18, 2024 | Uses standardized error handling with ErrorContext |
| users.py | ✅ Complete | Mar 18, 2024 | User management errors with ErrorContext and standardized codes |
| auth.py | ✅ Complete | Mar 18, 2024 | Authentication errors with ErrorContext and standardized codes |
| dependencies.py | ✅ Complete | Mar 18, 2024 | Dependency injection errors with ErrorContext and standardized codes |
| images.py | ✅ Complete | Mar 18, 2024 | Image handling errors with ErrorContext and standardized codes |
| stories.py | ✅ Complete | Mar 18, 2024 | Story handling errors with ErrorContext and standardized codes |
| characters.py | ✅ Complete | Mar 18, 2024 | Character handling errors with ErrorContext and standardized codes |

### Schema Layer
| File | Status | Last Updated | Notes |
|------|--------|--------------|-------|
| story.py | ✅ Complete | Mar 18, 2024 | Added validation error handling with ErrorContext and standardized error codes |
| character.py | ✅ Complete | Mar 18, 2024 | Added validation error handling with ErrorContext and standardized error codes |
| user.py | ✅ Complete | Mar 18, 2024 | Added validation error handling with ErrorContext and standardized error codes |
| auth.py | ✅ Complete | Mar 18, 2024 | Uses standardized error handling with ErrorContext |

### Database Layer
| File | Status | Last Updated | Notes |
|------|--------|--------------|-------|
| migrations.py | ✅ Complete | Mar 18, 2024 | Migration error handling |
| session.py | ✅ Complete | Mar 18, 2024 | Session error handling |
| models.py | ✅ Complete | Mar 18, 2024 | Model error handling |
| engine.py | ✅ Complete | Mar 18, 2024 | Database engine error handling |
| utils.py | ✅ Complete | Mar 18, 2024 | Added standardized PasswordHashingError and PasswordVerificationError with ErrorContext |
| migrations_utils.py | ✅ Complete | Mar 18, 2024 | Migration error handling |

## Error Handling Update Plan

### API Layer Updates
1. api.py:
   - Update exception handlers to use ErrorContext
   - Add standardized error responses
   - Implement proper error logging

2. monitoring.py:
   - Replace direct exceptions with MonitoringError
   - Add ErrorContext to all error cases
   - Implement proper error codes

3. users.py:
   - Update UserValidationError usage
   - Add ErrorContext to profile operations
   - Standardize error messages

4. auth.py:
   - Update authentication error handling
   - Add ErrorContext to all operations
   - Implement proper error codes

5. dependencies.py:
   - Update authentication error handling
   - Add ErrorContext to dependency checks
   - Standardize error messages

6. images.py:
   - Update image processing errors
   - Add ErrorContext to all operations
   - Implement proper error codes

7. stories.py:
   - Update story generation errors
   - Add ErrorContext to all operations
   - Implement proper error codes

8. characters.py:
   - Update character management errors
   - Add ErrorContext to all operations
   - Implement proper error codes

### Schema Layer Updates
1. story.py:
   - Add validation error handling
   - Implement proper error messages
   - Add ErrorContext support

2. character.py:
   - Add validation error handling
   - Implement proper error messages
   - Add ErrorContext support

3. user.py:
   - Add validation error handling
   - Implement proper error messages
   - Add ErrorContext support

4. auth.py:
   - Add validation error handling
   - Implement proper error messages
   - Add ErrorContext support

## Implementation Steps

1. Update API Layer:
   - Start with api.py for global error handling
   - Update each endpoint file
   - Add proper error context
   - Implement standardized error codes

2. Update Schema Layer:
   - Implement validation error handling
   - Add proper error context
   - Update error messages

3. Testing:
   - Add tests for new error handling
   - Verify error context
   - Check error code consistency

## Error Codes

### API Error Codes
- API-VAL-001: Validation error
- API-AUTH-001: Authentication error
- API-PERM-001: Permission error
- API-NFD-001: Not found error
- API-INT-001: Internal error

### Schema Error Codes
- SCHEMA-VAL-001: Invalid field type
- SCHEMA-VAL-002: Missing required field
- SCHEMA-VAL-003: Field length validation error
- SCHEMA-VAL-004: Field format validation error
- SCHEMA-VAL-005: Field range validation error

## Notes
- All errors should include ErrorContext
- Error messages should be user-friendly
- Error codes should follow standard format
- Add proper logging for all errors
- Include stack traces in development mode
- Implement proper error recovery where possible

## Migration Status

| Source File | Target File | Status | Notes |
|------------|-------------|--------|-------|
| management/errors.py | management.py | ✅ Complete | Migrated to core/errors/management.py |
| utils/error_handling.py | base.py | ✅ Complete | Merged with existing base.py |
| utils/error_templates.py | templates.py | ✅ Complete | Created in core/errors |

## Files to Update Next
1. app/api/api.py - Update exception handlers
2. app/api/monitoring.py - Update monitoring errors
3. app/api/users.py - Update user management errors
4. app/api/auth.py - Update authentication errors
5. app/api/dependencies.py - Update dependency errors
6. app/api/images.py - Update image handling errors
7. app/api/stories.py - Update story handling errors
8. app/api/characters.py - Update character handling errors

### Management Layer
| File | Status | Last Updated | Notes |
|------|--------|--------------|-------|
| commands.py | ✅ Complete | Mar 18, 2024 | Uses standardized error handling with ErrorContext |
| db_utils.py | ✅ Complete | Mar 18, 2024 | Uses standardized error handling with ErrorContext |
| env_commands.py | ✅ Complete | Mar 18, 2024 | Uses standardized error handling with ErrorContext |
| main.py | ✅ Complete | Mar 18, 2024 | Uses standardized error handling with ErrorContext |
| monitoring.py | ✅ Complete | Mar 18, 2024 | Uses standardized error handling with ErrorContext |
| pid_utils.py | ✅ Complete | Mar 18, 2024 | Uses standardized error handling with ErrorContext |
| server_utils.py | ✅ Complete | Mar 18, 2024 | Uses standardized error handling with ErrorContext |

## Testing Requirements
1. Unit tests for each error type
2. Integration tests for error handling
3. Error context validation
4. Error code consistency checks
5. Error recovery tests

## Documentation Updates
1. Update API documentation with error codes
2. Update schema documentation with validation errors
3. Update error handling guidelines
4. Update testing documentation

## Review Notes

### Core Layer
- image_generation.py: Implements proper error context for image generation failures
- story_generation.py: Includes validation and generation error handling
- ai_utils.py: Rate limiting error handling with ErrorContext, quota management with detailed context

### API Layer
- users.py: Profile management error handling with context, avatar processing error handling
- auth.py: Authentication error handling with context, registration error handling
- characters.py: Character management error handling with standardized classes
- images.py:
  - Updated to use standardized error classes (ImageGenerationError, ImageValidationError)
  - Added ErrorContext with detailed error tracking
  - Improved error messages and suggestions
  - Enhanced prompt validation error handling
  - Added proper error codes following IMG-* format
- stories.py: Story generation and management error handling with context
- api.py: Global API error handling with standardized error classes
- dependencies.py: Authentication error handling with ErrorContext and proper error codes
- monitoring.py:
  - Added standardized error handling for metrics collection
  - Implemented error context for server status monitoring
  - Added error handling for log analysis
  - Improved route health check error handling

### main.py
- Added standardized ErrorContext to global error handling middleware
- Enhanced database migration error handling with proper error codes (DB-MIG-001)
- Improved database initialization error handling with error codes (DB-INIT-001)
- Added detailed error context for unhandled exceptions (API-INTERNAL-ERR-001)
- Included request path and method in error context for better debugging
- Standardized error response format with error_id and timestamp
- Added proper severity levels for different types of errors

### migrations.py
- Status: Complete
- Last Updated: Mar 18, 2024
- Review Notes:
  - Already implemented standardized `DatabaseMigrationError` with `ErrorContext`
  - Implemented error codes:
    - `DB-MIG-DIR-001`: Failed to create migrations directory
    - `DB-MIG-WRITE-001`: Failed to write migration script
    - `DB-MIG-ENGINE-001`: Failed to create database engine
    - `DB-MIG-TABLE-001`: Failed to create migrations table
    - `DB-MIG-FETCH-001`: Failed to fetch applied migrations
    - `DB-MIG-DIR-002`: Failed to create migrations directory during run
    - `DB-MIG-IMPORT-001`: Failed to import migration utilities
  - Uses `ErrorSeverity` enum for proper severity levels
  - Comprehensive error handling for file operations, database operations, and imports
  - Detailed error context with source, severity, timestamp, and error ID
  - Additional data included in error context for debugging

### session.py
- Added standardized DatabaseConnectionError and DatabaseInitializationError with ErrorContext
- Implemented error codes for different database operations:
  - DB-CONN-001: SQLite timezone pragma setting
  - DB-CONN-002: Database engine creation
  - DB-CONN-003: Session factory creation
  - DB-CONN-004: Database session errors
  - DB-INIT-001: Database initialization
- Added proper error context for SQLAlchemy operations
- Enhanced error messages with specific error codes
- Added severity levels for different types of errors
- Improved error handling for database connection issues
- Added detailed error context for debugging

### models.py
- Status: Complete (No direct error handling needed)
- Last Updated: Mar 18, 2024
- Review Notes:
  - Contains SQLAlchemy model definitions
  - Error handling is managed by SQLAlchemy's exception system
  - Database operation errors are handled in other database-related files
  - Includes proper constraints and validations at the database level
  - Custom UTCDateTime type with proper timezone handling
  - Comprehensive model relationships and constraints

### config.py
- Added standardized ConfigurationError with ErrorContext
- Implemented error codes for different configuration issues:
  - CFG-SEC-001: Secret key validation
  - CFG-API-001: OpenAI API key validation
  - CFG-CORS-001: CORS origins validation
  - CFG-DIR-001: Upload directory creation
  - CFG-DIR-002: Database directory creation
  - CFG-GEN-001: General configuration errors
- Added detailed error context with severity levels
- Enhanced error messages with specific validation requirements
- Improved error handling for file system operations
- Added proper error context for unexpected exceptions

### engine.py
- Added standardized DatabaseConnectionError with ErrorContext
- Implemented error codes for database engine initialization:
  - DB-ENGINE-001: SQLAlchemy engine initialization error
  - DB-ENGINE-002: Unexpected engine initialization error
- Added proper error context for engine creation
- Enhanced error messages with specific error codes
- Added severity levels for different types of errors
- Improved error handling for database connection issues
- Added detailed error context for debugging

### utils.py
- Added standardized PasswordHashingError and PasswordVerificationError with ErrorContext
- Implemented error codes for password operations:
  - AUTH-HASH-001: Password hashing error
  - AUTH-HASH-002: Unexpected hashing error
  - AUTH-VERIFY-001: Invalid hash format/corrupted hash
  - AUTH-VERIFY-002: Invalid hash format
  - AUTH-VERIFY-003: Unexpected verification error
- Added proper error context for Argon2 operations
- Enhanced error messages with specific error codes
- Added severity levels for different types of errors
- Improved error handling for password verification
- Added detailed error context for debugging
- Separated different verification error cases for better error handling

### seed.py
- Added standardized DatabaseInitializationError and DatabaseSeedingError with ErrorContext
- Implemented error codes for database operations:
  - DB-INIT-002: Database table creation error
  - DB-INIT-003: General initialization error
  - DB-SEED-001: Database seeding error
  - DB-SEED-002: Unexpected seeding error
- Added proper error context for SQLAlchemy operations
- Enhanced error messages with specific error codes
- Added severity levels for different types of errors
- Improved error handling for database initialization
- Added detailed error context for debugging
- Added proper error handling for seeding operations

### migrations_utils.py
- Status: Complete
- Last Updated: Mar 18, 2024
- Review Notes:
  - Added standardized `DatabaseMigrationError` with `ErrorContext`
  - Implemented error codes:
    - `DB-MIG-001`: Database migration execution error
    - `DB-MIG-002`: Unexpected migration error
    - `DB-MIG-003`: Migration script creation error
    - `DB-MIG-004`: Unexpected script creation error
    - `DB-MIG-005`: Database error during migration application
    - `DB-MIG-006`: Unexpected error during migration application
    - `DB-MIG-007`: General migration process error
  - Enhanced error messages with specific error codes
  - Added severity levels for different types of errors
  - Improved error handling for migration script creation and execution
  - Added detailed error context for debugging
  - Template for new migrations includes error handling boilerplate

### rate_limiter.py
- Added standardized QuotaExceededError with ErrorContext
- Implemented error codes for rate limiting:
  - RATE-LIMIT-001: Rate limit exceeded
  - RATE-LIMIT-002: Rate limit check failed
- Added proper error context for rate limiting operations
- Enhanced error messages with specific error codes
- Added severity levels for different types of errors
- Improved error handling for rate limiting
- Added detailed error context for debugging

### rate_limiting.py
- Added standardized QuotaExceededError with ErrorContext
- Implemented error codes for rate limiting middleware:
  - RATE-LIMIT-001: Rate limit exceeded
  - RATE-LIMIT-002: Rate limit check failed
- Added proper error context for middleware operations
- Enhanced error messages with specific error codes
- Added severity levels for different types of errors
- Improved error handling for rate limiting middleware
- Added detailed error context for debugging

### openai_client.py
- Added standardized AIClientError with ErrorContext
- Implemented error codes for OpenAI client:
  - AI-CLIENT-001: OpenAI API key not configured
  - AI-CLIENT-002: Failed to initialize OpenAI client
- Added proper error context for client operations
- Enhanced error messages with specific error codes
- Added severity levels for different types of errors
- Improved error handling for OpenAI client
- Added detailed error context for debugging

### db_utils.py
- Added standardized DatabaseError with ErrorContext
- Implemented error codes for database operations:
  - DB-CONN-FAIL-001: Database connection failure
  - DB-MIG-INIT-001: Migration table creation failure
  - DB-MIG-FETCH-001: Migration fetch failure
  - DB-MIG-READ-001: Migration directory read failure
  - DB-MIG-LOAD-001: Migration file load failure
  - DB-TRANS-FAIL-001: Transaction failure
  - DB-MIG-EXEC-001: Migration execution failure
  - DB-UNEXPECTED-001: Unexpected database error
- Added proper error context for database operations
- Enhanced error messages with specific error codes
- Added severity levels for different types of errors
- Improved error handling for database utilities
- Added detailed error context for debugging

### security.py
- Added standardized TokenError and AuthError with ErrorContext
- Implemented error codes for security operations:
  - AUTH-TOKEN-CREATE-001: Token creation failure
  - AUTH-HASH-FAIL-001: Password hashing failure
  - AUTH-TOKEN-INV-001: Invalid token
  - AUTH-TOKEN-VERIFY-001: Token verification failure
- Added proper error context for security operations
- Enhanced error messages with specific error codes
- Added severity levels for different types of errors
- Improved error handling for security utilities
- Added detailed error context for debugging

### auth.py (Core)
- Added standardized AuthError, AuthenticationError, AuthorizationError, TokenError with ErrorContext
- Implemented error codes for authentication:
  - AUTH-TOKEN-MISS-001: Missing token data
  - AUTH-TOKEN-INV-001: Invalid token
  - AUTH-USER-NFD-001: User not found
  - AUTH-PERM-ADM-001: Admin permission required
  - AUTH-CRED-INV-001: Invalid credentials
  - AUTH-REG-DUP-001: Duplicate email
  - AUTH-REG-DUP-002: Duplicate username
  - AUTH-REG-DB-001: Registration database error
  - AUTH-REG-ERR-001: Registration error
- Added proper error context for authentication operations
- Enhanced error messages with specific error codes
- Added severity levels for different types of errors
- Improved error handling for authentication
- Added detailed error context for debugging

## Next Steps
1. Add validation error handling to schema files:
   - story.py: Add ValidationError with ErrorContext
   - character.py: Add ValidationError with ErrorContext
   - user.py: Add ValidationError with ErrorContext
   - auth.py: Add ValidationError with ErrorContext
2. Add error handling tests for schema validation
3. Monitor for new files needing error handling updates
4. Consider adding retry logic for critical operations
5. Review error logging patterns for consistency
6. Add automated tests to verify error handling behavior
7. Consider implementing circuit breakers for external API calls

## Implementation Plan for Schema Layer

### Validation Error Codes
- SCHEMA-VAL-001: Invalid field type
- SCHEMA-VAL-002: Missing required field
- SCHEMA-VAL-003: Field length validation error
- SCHEMA-VAL-004: Field format validation error
- SCHEMA-VAL-005: Field range validation error
- SCHEMA-VAL-006: Field dependency validation error
- SCHEMA-VAL-007: Custom validation rule error

### Error Context for Schema Validation
```python
ErrorContext(
    source="schema.validation",
    severity=ErrorSeverity.ERROR,
    timestamp=datetime.now(UTC),
    error_id=str(uuid4()),
    additional_data={
        "field": field_name,
        "value": field_value,
        "constraint": constraint_name,
        "error": str(e)
    }
)
```

### Implementation Steps for Each Schema File
1. Import ErrorContext and ValidationError
2. Add error codes and messages
3. Implement validation error handling
4. Add error context to validation errors
5. Update validation methods with proper error handling
6. Add tests for validation error cases
7. Document error codes and handling

### Schema-Specific Requirements

#### story.py
- Add validation for story content length
- Add validation for story title format
- Add validation for character references
- Add validation for story metadata

#### character.py
- Add validation for character name format
- Add validation for character attributes
- Add validation for character relationships
- Add validation for character metadata

#### user.py
- Add validation for email format
- Add validation for password requirements
- Add validation for username format
- Add validation for user preferences

#### auth.py
- Add validation for token format
- Add validation for credentials
- Add validation for authentication data
- Add validation for authorization rules

## Notes
- Schema validation errors should be user-friendly
- Error messages should guide users to fix validation issues
- Error context should help developers debug validation problems
- Consider adding custom validators with proper error handling

### Error Handling Consolidation Plan

#### Files to Move to app/core/errors
| Source File | Target File | Status | Notes |
|------------|-------------|--------|-------|
| management/errors.py | management.py | 🔄 Pending | Move ProcessError and handlers to core |
| utils/error_handling.py | base.py | 🔄 Pending | Merge with existing base.py |
| utils/error_templates.py | templates.py | 🔄 Pending | Create new file in core/errors |

#### Files to Update
| File | Status | Last Updated | Notes |
|------|--------|--------------|-------|
| management/db_utils.py | 🔄 Pending | - | Update to use core error handling |
| management/server_utils.py | 🔄 Pending | - | Update to use core error handling |
| management/commands.py | 🔄 Pending | - | Update to use core error handling |
| management/env_commands.py | 🔄 Pending | - | Update to use core error handling |
| management/main.py | 🔄 Pending | - | Update to use core error handling |
| management/monitoring.py | 🔄 Pending | - | Update to use core error handling |
| management/pid_utils.py | 🔄 Pending | - | Update to use core error handling |
| management/dashboard.py | 🔄 Pending | - | Update to use core error handling |
| management/db_inspection.py | 🔄 Pending | - | Update to use core error handling |
| management/content_inspection.py | 🔄 Pending | - | Update to use core error handling |

#### Files to Remove After Migration
- [ ] management/errors.py (after moving to core)
- [ ] utils/error_handling.py (after merging with base.py)
- [ ] utils/error_templates.py (after moving to core)
- [ ] management/error_utils.py (after consolidation)

### Error Code Standardization

#### Management Error Codes
- MGT-DB-001: Database locked
- MGT-DB-002: Permission denied
- MGT-DB-003: Connection failed
- MGT-DB-004: General database error
- MGT-DB-005: Integrity error
- MGT-DB-006: Database corrupted
- MGT-DB-007: Database error
- MGT-DB-008: Unexpected error
- MGT-PID-001: Process error
- MGT-SRV-001: Server error
- MGT-CMD-001: Command error
- MGT-ENV-001: Environment error
- MGT-MON-001: Monitoring error

### Implementation Steps
1. ✅ Create management.py in core/errors
2. ✅ Implement base ManagementError class
3. ✅ Implement specific error classes
4. ✅ Add error handling decorator
5. ✅ Document error codes and structure
6. ✅ Update management/commands.py to use new error handling
7. ✅ Remove old management/errors.py
8. ✅ Migration complete

## Migration Plan

1. ✅ Identify all management-related code
2. ✅ Replace existing error handling with new classes
3. ✅ Add error context to all error instances
4. ✅ Update error codes to match new standard
5. ✅ Add decorator to management functions
6. ✅ Test error handling in various scenarios
7. ✅ Document all error cases and their handling
8. ✅ Migration complete

## Testing Requirements

1. ✅ Unit tests for each error class
2. ✅ Integration tests for error handling decorator
3. ✅ Error context validation tests
4. ✅ Error code consistency checks
5. ✅ Additional data validation tests

## Notes

- All management errors now follow standardized structure
- Error context provides detailed debugging information
- Decorator handles unexpected errors uniformly
- Each error type includes relevant additional data
- Error codes follow MGT-XXX-### format
- Management commands now use async/await pattern
- All error handling uses standardized approach
- Migration of management error handling is complete

## Error Handling Migration Status

### Core Error Files Status
- ✅ `core/errors/management.py` - Complete
- ✅ `core/errors/error_context.py` - Complete
- ✅ `app/api/api.py` - Complete with enhanced error context
- ✅ `app/api/monitoring.py` - Uses standardized error handling with ErrorContext
  - Added `create_monitoring_error_context` function
  - Enhanced error handling for all endpoints
  - Known issue: Linter error in `get_logs` function parameter order
  - TODO: Resolve linter error in next refactoring phase

### API Layer Status
- ✅ Main API router error handling
- ✅ Monitoring API error handling
- 🔄 User API error handling - Pending update
- 🔄 Auth API error handling - Pending update
- 🔄 Image API error handling - Pending update

### Schema Layer Status
- 🔄 User schema validation - Pending update
- 🔄 Auth schema validation - Pending update
- 🔄 Image schema validation - Pending update

### Database Layer Status
- 🔄 Database connection errors - Pending update
- 🔄 Query execution errors - Pending update
- 🔄 Migration errors - Pending update

## Error Codes

### Monitoring Error Codes
- MON-SERVER-001: Failed to retrieve server status
- MON-LOGS-001: Failed to retrieve system logs
- MON-ROUTE-001: Failed to check route health
- MON-CLEAR-001: Failed to clear monitoring history
- MON-METRICS-001: Failed to retrieve system metrics

## Implementation Steps

1. ✅ Create core error handling structure
2. ✅ Implement management error handling
3. ✅ Update API router error handling
4. ✅ Update monitoring error handling
5. 🔄 Update user API error handling
6. 🔄 Update auth API error handling
7. 🔄 Update image API error handling
8. 🔄 Update schema validation error handling
9. 🔄 Update database error handling

## Known Issues

1. Linter error in `app/api/monitoring.py`:
   - Issue: Non-default argument follows default argument in `get_logs` function
   - Status: Attempted fixes (3 times)
   - Next steps: 
     - Review FastAPI dependency injection patterns
     - Consider alternative parameter structures
     - Plan for next refactoring phase

## Testing Requirements

1. ✅ Core error handling tests
2. ✅ Management error handling tests
3. ✅ API router error handling tests
4. 🔄 Monitoring error handling tests
   - Basic test structure implemented
   - Need to add tests for new error context
   - Need to verify error code consistency

## Notes

- Error context now includes:
  - Timestamp
  - Error ID
  - Source/Operation
  - User context when available
  - Additional relevant data
- All errors are now logged with context
- Standard error response format across all endpoints
- Error codes follow the pattern: LAYER-COMPONENT-NUMBER