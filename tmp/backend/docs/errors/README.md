# Error Documentation

This directory contains comprehensive documentation for all error types, their handling, and recovery procedures across the system.

## Contents

### Core Errors
- [`_base_errors.md`](_base_errors.md): Base error types and patterns
- [`_validation_errors.md`](_validation_errors.md): Input validation errors

### Infrastructure Errors
- [`_database_errors.md`](_database_errors.md): Database-related errors
- [`_rate_limit_errors.md`](_rate_limit_errors.md): Rate limiting errors
- [`_auth_errors.md`](_auth_errors.md): Authentication errors

### Domain Errors
- [`_api_errors.md`](_api_errors.md): General API errors
- [`_user_errors.md`](_user_errors.md): User management errors
- [`_character_errors.md`](_character_errors.md): Character-related errors
- [`_story_errors.md`](_story_errors.md): Story generation errors
- [`_image_errors.md`](_image_errors.md): Image generation errors

## Error Documentation Structure

Each error documentation follows this structure:
1. **Overview**: Error category description
2. **Error Types**: List of specific errors
   - Error code pattern
   - Description
   - Possible causes
   - Impact
3. **Error Handling**:
   - Detection
   - Recovery steps
   - Prevention
4. **Examples**: Real-world examples
5. **Best Practices**: Error handling guidelines

## Error Code Pattern

Our error codes follow this format: `DOMAIN-TYPE-CODE`
- **DOMAIN**: System area (e.g., DB, API, AUTH)
- **TYPE**: Error type (e.g., CONN, VALID, PERM)
- **CODE**: Unique identifier (e.g., 001, 002)

Example: `DB-CONN-001` for database connection error

## Usage Guidelines

1. Use consistent error patterns
2. Include all error properties
3. Document recovery steps
4. Provide practical examples
5. Keep error codes unique
6. Update when adding new errors
7. Cross-reference related errors 