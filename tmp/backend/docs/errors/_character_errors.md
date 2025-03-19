# Character Error Handling Documentation

## File: `app/core/errors/character.py`

### Overview
Defines character-specific error classes for handling various character-related operations in the story generation system.

### Error Classes

#### CharacterError
- **Purpose**: Base class for all character-related errors
- **Error Code Pattern**: CHAR-*
- **Status Code**: 500 (default)
- **Usage**: Base class, not used directly

#### CharacterCreationError
- **Purpose**: Handle character creation process failures
- **Error Code**: CHAR-CREATE-FAIL-001
- **Status Code**: 500
- **Usage**: Character creation process errors
- **Details**: Includes creation_step information
- **Suggestions**:
  - Check character parameters
  - Verify creation guidelines
  - Review character constraints

#### CharacterValidationError
- **Purpose**: Handle character validation failures
- **Error Code**: CHAR-VAL-FAIL-001
- **Status Code**: 422
- **Usage**: Character validation errors
- **Details**: Includes validation_issue information
- **Suggestions**:
  - Check character attributes
  - Verify age appropriateness
  - Review character complexity

#### CharacterPersistenceError
- **Purpose**: Handle character saving/loading failures
- **Error Code**: CHAR-PERS-FAIL-001
- **Status Code**: 500
- **Usage**: Storage operation errors
- **Details**: Includes character_id and operation information
- **Suggestions**:
  - Check storage system status
  - Verify character data integrity
  - Ensure proper permissions

#### CharacterInteractionError
- **Purpose**: Handle character interaction and behavior failures
- **Error Code**: CHAR-INTER-FAIL-001
- **Status Code**: 500
- **Usage**: Character interaction errors
- **Details**: Includes interaction_type information
- **Suggestions**:
  - Check interaction rules
  - Verify character compatibility
  - Review behavior constraints

### Code Structure Analysis

#### Inheritance Pattern
All errors inherit from BaseError, providing:
- Consistent error formatting
- Standard HTTP status codes
- Unified error handling
- Severity levels
- Detailed context

#### Error Code Pattern
Standardized format: CHAR-[CATEGORY]-[SPECIFIC]-[NUMBER]
Examples:
- CHAR-CREATE-FAIL-001
- CHAR-VAL-FAIL-001
- CHAR-PERS-FAIL-001
- CHAR-INTER-FAIL-001

### Best Practices

#### Error Creation
1. Always provide specific error messages
2. Include relevant context (creation step, validation issue, etc.)
3. Set appropriate severity level
4. Add detailed suggestions for resolution
5. Use consistent error codes

#### Error Handling
1. Log detailed error information
2. Include operation context
3. Provide recovery suggestions
4. Set appropriate HTTP status codes
5. Monitor error patterns

### Integration Points

#### Character Creation Service
```python
def create_character(params: Dict[str, Any]) -> None:
    try:
        return character_creator.create(params)
    except Exception as e:
        raise CharacterCreationError(
            message="Failed to create character",
            creation_step="attribute_generation",
            context=ErrorContext(
                user_id=params.get("user_id"),
                timestamp=datetime.now()
            )
        )
```

#### Character Validation Service
```python
def validate_character(character_data: Dict[str, Any]) -> None:
    try:
        validator.validate(character_data)
    except Exception as e:
        raise CharacterValidationError(
            message="Character validation failed",
            validation_issue="inappropriate_traits",
            context=ErrorContext(
                character_id=character_data.get("id"),
                timestamp=datetime.now()
            )
        )
```

### Monitoring Integration

#### Error Metrics
```python
class CharacterErrorTracker:
    def track_error(self, error: BaseError):
        if isinstance(error, CharacterCreationError):
            metrics.increment("character.creation.errors", 
                            tags={"step": error.details["creation_step"]})
        elif isinstance(error, CharacterValidationError):
            metrics.increment("character.validation.errors",
                            tags={"issue": error.details["validation_issue"]})
```

### Testing Requirements

#### Test Scenarios
1. Creation failures at different steps
2. Validation error cases
3. Storage operation failures
4. Interaction error scenarios
5. Error context validation

#### Error Recovery Tests
1. Verify error suggestions
2. Test severity levels
3. Validate error details
4. Check HTTP status codes
5. Test error tracking

### Future Enhancements
1. Add more specific error types for different creation steps
2. Implement retry mechanisms for transient failures
3. Add circuit breakers for external services
4. Enhance error tracking and analytics
5. Improve error recovery suggestions based on patterns 