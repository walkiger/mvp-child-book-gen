# Characters API Documentation

## Overview
The Characters API (`app/api/characters.py`) provides endpoints for character creation, management, and image generation. It includes real-time progress tracking, image selection, and character refinement capabilities, with comprehensive error handling and logging.

## Error Handling

### Error Classes
1. **CharacterError**
   - Base error for character operations
   - Used for unexpected errors
   - Includes error context and severity

2. **CharacterNotFoundError**
   - Raised when character doesn't exist
   - Includes character ID and user context
   - HTTP Status: 404

3. **CharacterCreationError**
   - Raised during character creation failures
   - Includes character and user context
   - HTTP Status: 500

4. **CharacterImageError**
   - Raised during image processing issues
   - Includes image generation context
   - HTTP Status: 500

5. **CharacterValidationError**
   - Raised for invalid character data
   - Includes validation context
   - HTTP Status: 400

6. **CharacterUpdateError**
   - Raised during character update failures
   - Includes update context
   - HTTP Status: 500

7. **CharacterDeletionError**
   - Raised during character deletion failures
   - Includes deletion context
   - HTTP Status: 500

### Error Context
All errors include:
- Timestamp
- Error ID (UUID)
- Source operation
- Severity level
- Additional data (user ID, character ID, etc.)

### Error Examples
```python
# Character not found
raise CharacterNotFoundError(
    character_id=character_id,
    context=ErrorContext(
        source="characters.get_character",
        severity=ErrorSeverity.WARNING,
        timestamp=datetime.now(UTC),
        error_id=str(uuid4()),
        additional_data={"user_id": current_user.id}
    )
)

# Character creation error
raise CharacterCreationError(
    message="Failed to create character",
    context=ErrorContext(
        source="characters.create_character",
        severity=ErrorSeverity.ERROR,
        timestamp=datetime.now(UTC),
        error_id=str(uuid4()),
        additional_data={
            "user_id": current_user.id,
            "character_name": character.name,
            "error": str(e)
        }
    )
)

# Image processing error
raise CharacterImageError(
    message="Failed to process character image",
    context=ErrorContext(
        source="characters.process_image",
        severity=ErrorSeverity.ERROR,
        timestamp=datetime.now(UTC),
        error_id=str(uuid4()),
        additional_data={
            "character_id": character_id,
            "image_index": image_index,
            "error": str(e)
        }
    )
)
```

## Endpoints

### Character Management
1. **Create Character** (`POST /`)
   - Creates new character with generated images
   - Handles image generation and storage
   - Tracks generation progress
   - Supports DALL-E version selection
   - Error handling:
     - `CharacterCreationError`: Creation failure
     - `CharacterImageError`: Image generation failure
     - `CharacterValidationError`: Invalid input data

2. **Get Generation Status** (`GET /{character_id}/generation-status`)
   - Server-sent events for real-time updates
   - Tracks image generation progress
   - Provides generated image URLs
   - Reports completion status
   - Error handling:
     - `CharacterNotFoundError`: Invalid character
     - `CharacterError`: Progress tracking failure

3. **Select Character Image** (`POST /{character_id}/select-image`)
   - Selects primary character image
   - Validates image selection
   - Updates character profile
   - Handles image references
   - Error handling:
     - `CharacterNotFoundError`: Invalid character
     - `CharacterValidationError`: Invalid image index
     - `CharacterUpdateError`: Image selection failure

4. **Regenerate Images** (`POST /{character_id}/regenerate`)
   - Regenerates character images
   - Preserves character data
   - Tracks generation progress
   - Updates image references
   - Error handling:
     - `CharacterNotFoundError`: Invalid character
     - `CharacterImageError`: Generation failure
     - `CharacterUpdateError`: Update failure

### Character Operations
1. **Get User Characters** (`GET /`)
   - Lists all user characters
   - Includes image references
   - Provides character metadata
   - Filters by user
   - Error handling:
     - `CharacterError`: Database query failure

2. **Get Character** (`GET /{character_id}`)
   - Retrieves character details
   - Validates access rights
   - Returns complete data
   - Includes image URLs
   - Error handling:
     - `CharacterNotFoundError`: Invalid character
     - `CharacterError`: Retrieval failure

3. **Update Character** (`PUT /{character_id}`)
   - Updates character metadata
   - Validates changes
   - Maintains consistency
   - Preserves images
   - Error handling:
     - `CharacterNotFoundError`: Invalid character
     - `CharacterValidationError`: Invalid update data
     - `CharacterUpdateError`: Update failure

4. **Delete Character** (`DELETE /{character_id}`)
   - Removes character data
   - Deletes associated images
   - Validates permissions
   - Handles cleanup
   - Error handling:
     - `CharacterNotFoundError`: Invalid character
     - `CharacterDeletionError`: Deletion failure

### Character Enhancement
1. **Generate Single Image** (`POST /{character_id}/generate-image`)
   - Creates additional image
   - Uses existing traits
   - Updates image collection
   - Tracks generation
   - Error handling:
     - `CharacterNotFoundError`: Invalid character
     - `CharacterImageError`: Generation failure
     - `CharacterUpdateError`: Image update failure

2. **Enhance Prompt** (`POST /{character_id}/enhance-prompt`)
   - Improves image prompts
   - Refines character traits
   - Updates generation parameters
   - Optimizes results
   - Error handling:
     - `CharacterNotFoundError`: Invalid character
     - `CharacterUpdateError`: Enhancement failure

3. **Refine Character** (`POST /{character_id}/refine`)
   - Enhances character details
   - Updates traits
   - Regenerates images
   - Improves quality
   - Error handling:
     - `CharacterNotFoundError`: Invalid character
     - `CharacterValidationError`: Invalid refinement data
     - `CharacterUpdateError`: Refinement failure

4. **Check Name** (`GET /check-name`)
   - Validates character names
   - Checks uniqueness
   - Prevents duplicates
   - Returns availability
   - Error handling:
     - `CharacterValidationError`: Invalid name format
     - `CharacterError`: Validation failure

## Best Practices
1. Always check character ownership
2. Validate input parameters
3. Handle transaction rollbacks
4. Include error context
5. Log operations and errors
6. Track operation progress
7. Maintain data consistency

## Integration Points
1. Database operations
2. OpenAI client
3. Image generation
4. Error handling system
5. Progress tracking
6. Logging system
7. Storage management

## Testing Requirements
1. Test all error scenarios
2. Validate error context
3. Check transaction rollbacks
4. Verify progress tracking
5. Test input validation
6. Check ownership validation
7. Verify error logging

## Future Improvements
1. **Short-term**
   - Enhanced validation
   - Better error messages
   - Progress tracking
   - Image optimization

2. **Long-term**
   - Batch operations
   - Advanced generation
   - Style transfer
   - Animation support 