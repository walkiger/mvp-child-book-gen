# Stories API Documentation

## Overview
The Stories API (`app/api/stories.py`) provides endpoints for story creation, management, and generation. It includes functionality for creating stories, generating images, managing story content, and handling various story-related operations, with comprehensive error handling and logging.

## Error Handling

### Error Classes
1. **StoryError**
   - Base error for story operations
   - Used for unexpected errors
   - Includes error context and severity

2. **StoryNotFoundError**
   - Raised when story doesn't exist
   - Includes story ID and user context
   - HTTP Status: 404

3. **StoryCreationError**
   - Raised during story creation failures
   - Includes character and user context
   - HTTP Status: 500

4. **StoryGenerationError**
   - Raised during content generation issues
   - Includes generation parameters
   - HTTP Status: 500

5. **StoryValidationError**
   - Raised for invalid story data
   - Includes validation context
   - HTTP Status: 400

6. **StoryUpdateError**
   - Raised during story update failures
   - Includes update context
   - HTTP Status: 500

7. **StoryDeletionError**
   - Raised during story deletion failures
   - Includes deletion context
   - HTTP Status: 500

### Error Context
All errors include:
- Timestamp
- Error ID (UUID)
- Source operation
- Severity level
- Additional data (user ID, story ID, etc.)

### Error Examples
```python
# Story not found
raise StoryNotFoundError(
    story_id=story_id,
    context=ErrorContext(
        source="stories.get_story",
        severity=ErrorSeverity.WARNING,
        timestamp=datetime.now(UTC),
        error_id=str(uuid4()),
        additional_data={"user_id": current_user.id}
    )
)

# Story generation error
raise StoryGenerationError(
    message="Failed to generate story content",
    context=ErrorContext(
        source="stories.generate_story_endpoint",
        severity=ErrorSeverity.ERROR,
        timestamp=datetime.now(UTC),
        error_id=str(uuid4()),
        additional_data={
            "character_id": character.id,
            "user_id": current_user.id,
            "error": str(e)
        }
    )
)
```

## Endpoints

### Story Management
1. **Create Story** (`POST /`)
   - Creates a new story with generated content
   - Handles character validation
   - Manages story generation process
   - Tracks generation progress
   - Error handling:
     - `CharacterNotFoundError`: Invalid character
     - `StoryGenerationError`: Generation failure
     - `StoryCreationError`: Database errors

2. **Generate Images** (`POST /{story_id}/generate-images`)
   - Generates images for story pages
   - Validates story ownership
   - Handles image generation process
   - Error handling:
     - `StoryNotFoundError`: Invalid story
     - `StoryGenerationError`: Image generation failure

3. **Select Page Image** (`POST /{story_id}/select-page-image`)
   - Selects image for specific page
   - Validates page numbers
   - Updates story content
   - Error handling:
     - `StoryNotFoundError`: Invalid story
     - `StoryValidationError`: Invalid page number
     - `StoryUpdateError`: Image selection failure

4. **Update Page Text** (`PUT /{story_id}/page/{page_number}`)
   - Updates text content of specific page
   - Validates page existence
   - Maintains story integrity
   - Error handling:
     - `StoryNotFoundError`: Invalid story
     - `StoryValidationError`: Invalid page number
     - `StoryUpdateError`: Text update failure

### Story Operations
1. **Get User Stories** (`GET /`)
   - Lists all stories for current user
   - Includes character information
   - Provides story metadata
   - Error handling:
     - `StoryError`: Database query failure

2. **Get Story** (`GET /{story_id}`)
   - Retrieves specific story details
   - Validates story access
   - Returns complete story data
   - Error handling:
     - `StoryNotFoundError`: Invalid story
     - `StoryError`: Retrieval failure

3. **Update Story** (`PUT /{story_id}`)
   - Updates story metadata
   - Validates update permissions
   - Maintains data consistency
   - Error handling:
     - `StoryNotFoundError`: Invalid story
     - `StoryUpdateError`: Update failure

4. **Delete Story** (`DELETE /{story_id}`)
   - Removes story and associated data
   - Validates deletion permissions
   - Handles cleanup operations
   - Error handling:
     - `StoryNotFoundError`: Invalid story
     - `StoryDeletionError`: Deletion failure

### Story Enhancement
1. **Regenerate Story** (`POST /{story_id}/regenerate`)
   - Regenerates story content and images
   - Updates story status
   - Tracks regeneration progress
   - Error handling:
     - `StoryNotFoundError`: Invalid story
     - `CharacterNotFoundError`: Missing character
     - `StoryGenerationError`: Regeneration failure

2. **Enhance Story** (`POST /{story_id}/enhance`)
   - Enhances story content
   - Updates story status
   - Tracks enhancement progress
   - Error handling:
     - `StoryNotFoundError`: Invalid story
     - `StoryGenerationError`: Enhancement failure

## Best Practices
1. Always check story ownership
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
4. Character management
5. Error handling system
6. Progress tracking
7. Logging system

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
   - Content versioning
   - Advanced generation
   - Performance optimization 