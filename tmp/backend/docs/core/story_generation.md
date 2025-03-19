# Story Generation Documentation

## Overview
The Story Generation module provides functionality for generating children's stories using OpenAI's GPT-4, with robust error handling, content validation, and age-appropriate content management.

## Components

### Story Generation
Core story generation functionality:

```python
async def generate_story(
    client: AsyncOpenAI,
    character_name: str,
    character_traits: list,
    title: str,
    age_group: str,
    page_count: int,
    story_tone: str,
    moral_lesson: str = None
) -> Dict[str, Any]:
    """Generate a children's story using GPT-4."""
```

Key features:
- Parameter validation
- OpenAI integration
- Content validation
- Structured error handling

### Input Validation
Validates story generation parameters:

```python
def _validate_story_params(
    age_group: str,
    story_tone: str,
    page_count: int
) -> None:
    """Validate story generation parameters."""
```

Validates:
- Age groups (1-2, 3-6, 6-9, 10-12)
- Story tones (whimsical, educational, adventurous, calming)
- Page count (5-30 pages)

### Content Validation
Validates generated story content:

```python
def _validate_story_content(
    content: Dict[str, Any]
) -> None:
    """Validate generated story content."""
```

Checks:
- Content structure
- Required fields
- Page formatting
- Field types

## Error Handling

### Error Classes

1. **StoryGenerationError**
   - Purpose: Handles story generation failures
   - Context: Includes generation step and error details
   - Example:
   ```python
   raise StoryGenerationError(
       message="Failed to generate story content",
       generation_step="api_call",
       context=context,
       details={"error": str(e)}
   )
   ```

2. **StoryValidationError**
   - Purpose: Handles content validation failures
   - Context: Includes content issue and validation details
   - Example:
   ```python
   raise StoryValidationError(
       message="Invalid age group",
       content_issue="age_group",
       context=context,
       details={
           "provided": age_group,
           "valid_options": valid_age_groups
       }
   )
   ```

### Error Patterns

1. **Parameter Validation**
   ```python
   try:
       _validate_story_params(age_group, story_tone, page_count)
   except StoryValidationError:
       # Parameter validation failed
       raise
   ```

2. **API Error Handling**
   ```python
   try:
       response = await client.chat.completions.create(...)
   except Exception as e:
       raise StoryGenerationError(
           message="Failed to generate story content",
           generation_step="api_call",
           context=context,
           details={"error": str(e)}
       )
   ```

3. **Content Validation**
   ```python
   try:
       story_content = json.loads(response.choices[0].message.content)
       _validate_story_content(story_content)
   except StoryValidationError:
       # Content validation failed
       raise
   ```

## Best Practices

1. **Error Management**
   - Use structured error classes
   - Include detailed context
   - Provide recovery suggestions
   - Log error details

2. **Content Generation**
   - Validate all inputs
   - Check content structure
   - Ensure age appropriateness
   - Maintain consistency

3. **API Integration**
   - Handle API errors
   - Validate responses
   - Manage rate limits
   - Monitor performance

## Integration Points
- OpenAI API Client
- Error Handler
- Rate Limiter
- Content Validator

## Testing Requirements

1. **Generation Testing**
   - Test parameter validation
   - Verify error handling
   - Check content generation
   - Test edge cases

2. **Content Testing**
   - Test content validation
   - Verify age appropriateness
   - Check story structure
   - Test field validation

3. **Integration Testing**
   - Test with OpenAI API
   - Verify error propagation
   - Check rate limiting
   - Test recovery flows

## Future Improvements

1. **Short-term**
   - Enhanced validation
   - Better error tracking
   - Content optimization
   - Performance monitoring

2. **Long-term**
   - Advanced story structures
   - ML-based validation
   - Content personalization
   - Multi-model support 