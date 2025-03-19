# Image Generation Module Documentation

## Overview
The Image Generation module (`image_generation.py`) provides functionality for generating images using OpenAI's DALL-E API, with robust error handling and validation. The module supports character image generation, story page illustrations, and prompt enhancement capabilities.

## Core Components

### 1. Circuit Breaker
- Implements a circuit breaker pattern for API calls
- Prevents cascading failures by stopping requests after multiple failures
- Auto-resets after a timeout period
- Raises `ImageGenerationError` when circuit is open

### 2. Retry Mechanism
- Implements exponential backoff retry for failed operations
- Configurable max attempts, delay, and backoff factor
- Handles transient failures gracefully
- Raises `ImageGenerationError` after max retries

### 3. OpenAI API Integration
```python
@with_retry(max_attempts=3, retry_delay=2.0, backoff_factor=2.0)
@openai_circuit_breaker
async def call_openai_image_api(
    client: AsyncOpenAI,
    model: str,
    prompt: str,
    size: str = "1024x1024",
    quality: str = "standard",
    n: int = 1,
    style: Optional[str] = None
) -> str:
    """
    Call OpenAI's image generation API with error handling.
    """
```

### 4. Character Image Generation
```python
async def generate_character_images(
    client: AsyncOpenAI,
    character_name: str,
    character_traits: list,
    dalle_version: str = "dall-e-3",
    progress_callback: Callable[[int, str], None] = None
) -> List[str]:
    """
    Generate character images with validation and error handling.
    """
```

### 5. Story Page Image Generation
```python
async def generate_story_page_images(
    client: AsyncOpenAI,
    story_content: dict,
    character_name: str,
    character_traits: list
) -> List[dict]:
    """
    Generate story page images with validation and error handling.
    """
```

## Error Handling

### Error Classes

1. `ImageGenerationError`
   - Purpose: Handles failures during image generation
   - Pattern: Raised for API failures, circuit breaker trips, and retry exhaustion
   - Example:
     ```python
     raise ImageGenerationError(
         message="Failed to generate image",
         generation_step="api_call",
         context=ErrorContext(
             source="image_generation.call_openai_image_api",
             severity=ErrorSeverity.ERROR
         ),
         details={"error": str(e)}
     )
     ```

2. `ImageProcessingError`
   - Purpose: Handles failures in processing API responses
   - Pattern: Raised for URL extraction failures and invalid response formats
   - Example:
     ```python
     raise ImageProcessingError(
         message="Failed to extract image URL from response",
         operation="url_extraction",
         image_format="url",
         context=context,
         details={"error": str(e)}
     )
     ```

3. `ImageValidationError`
   - Purpose: Handles input validation failures
   - Pattern: Raised for invalid parameters or data formats
   - Example:
     ```python
     raise ImageValidationError(
         message="Invalid character traits",
         validation_type="input",
         issue="character_traits",
         context=context,
         details={"provided": character_traits}
     )
     ```

### Error Patterns

1. Input Validation
   ```python
   if not character_name or not isinstance(character_name, str):
       raise ImageValidationError(
           message="Invalid character name",
           validation_type="input",
           issue="character_name",
           context=context,
           details={"provided": character_name}
       )
   ```

2. API Error Handling
   ```python
   try:
       response = await client.images.generate(...)
   except Exception as e:
       raise ImageGenerationError(
           message="Failed to generate image",
           generation_step="api_call",
           context=context,
           details={"error": str(e)}
       )
   ```

3. Response Processing
   ```python
   try:
       image_url = response.data[0].url
   except Exception as e:
       raise ImageProcessingError(
           message="Failed to extract image URL",
           operation="url_extraction",
           image_format="url",
           context=context,
           details={"error": str(e)}
       )
   ```

## Best Practices

### Error Management
1. Use appropriate error classes for different failure types
2. Include detailed context in error messages
3. Implement circuit breakers for external services
4. Use retry mechanisms with exponential backoff
5. Log errors with appropriate severity levels

### Image Generation
1. Validate all input parameters before API calls
2. Use appropriate DALL-E model versions
3. Implement progress callbacks for long operations
4. Maintain consistent image styles
5. Handle API rate limits gracefully

### Resource Management
1. Close API connections properly
2. Clean up temporary resources
3. Monitor API usage and quotas
4. Implement timeouts for API calls
5. Handle concurrent requests efficiently

## Integration Points

### OpenAI API Client
- Configuration management
- API key handling
- Rate limit monitoring
- Model version selection

### Error Handler
- Error logging and tracking
- Error aggregation
- Alert generation
- Error recovery strategies

### Progress Tracking
- Status updates
- Progress callbacks
- Event notifications
- Operation cancellation

## Testing Requirements

### Generation Testing
1. Test character image generation with various traits
2. Test story page image generation with different content
3. Test prompt enhancement with various inputs
4. Verify image URL formats and accessibility

### Error Testing
1. Test circuit breaker functionality
2. Test retry mechanism with different failure scenarios
3. Test input validation for all parameters
4. Test error handling for API failures

### Integration Testing
1. Test with OpenAI API client
2. Test with progress tracking system
3. Test with error handling system
4. Test concurrent operations

## Future Improvements

### Short-term
1. Add image format validation
2. Implement image content moderation
3. Add support for batch operations
4. Enhance prompt generation
5. Improve error recovery strategies

### Long-term
1. Support multiple image generation services
2. Implement advanced caching
3. Add image optimization pipeline
4. Enhance concurrent processing
5. Implement advanced rate limiting

## Common Utilities

### Prompt Enhancement
```python
async def enhance_image_prompt(
    client: AsyncOpenAI,
    name: str,
    traits: List[str],
    base_prompt: str
) -> str:
    """
    Enhance image generation prompts using GPT-4.
    """
```

### Image Validation
- Format validation
- Content validation
- Size validation
- Quality checks
- Style consistency checks 