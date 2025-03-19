"""
Image generation functionality using OpenAI's DALL-E.
"""

from typing import List, Callable, Optional
import asyncio
import logging
from openai import AsyncOpenAI

from .errors.image import (
    ImageGenerationError,
    ImageProcessingError,
    ImageValidationError
)
from .errors.base import ErrorContext, ErrorSeverity

# Set up logger
logger = logging.getLogger(__name__)

class CircuitBreaker:
    """Circuit breaker for API calls."""
    def __init__(self, name: str, failure_threshold: int = 3, reset_timeout: int = 300):
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.last_failure_time = None
        self.is_open = False

    def __call__(self, func):
        async def wrapper(*args, **kwargs):
            if self.is_open:
                raise ImageGenerationError(
                    message=f"Circuit breaker is open for {self.name}",
                    generation_step="circuit_breaker",
                    context=ErrorContext(
                        source="image_generation.CircuitBreaker",
                        severity=ErrorSeverity.ERROR
                    ),
                    details={
                        "failures": self.failures,
                        "reset_timeout": self.reset_timeout
                    }
                )
            try:
                result = await func(*args, **kwargs)
                self.failures = 0
                self.is_open = False
                return result
            except Exception as e:
                self.failures += 1
                if self.failures >= self.failure_threshold:
                    self.is_open = True
                raise
        return wrapper

# Circuit breaker for OpenAI API calls
openai_circuit_breaker = CircuitBreaker(
    name="OpenAI",
    failure_threshold=3,  # 3 failures will open the circuit
    reset_timeout=300     # Wait 5 minutes before trying again
)

def with_retry(max_attempts: int = 3, retry_delay: float = 2.0, backoff_factor: float = 2.0):
    """Retry decorator with exponential backoff."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            context = ErrorContext(
                source=f"image_generation.{func.__name__}",
                severity=ErrorSeverity.ERROR
            )
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise ImageGenerationError(
                            message="Max retry attempts reached",
                            generation_step="retry",
                            context=context,
                            details={
                                "attempts": attempt + 1,
                                "max_attempts": max_attempts,
                                "error": str(e)
                            }
                        )
                    delay = retry_delay * (backoff_factor ** attempt)
                    await asyncio.sleep(delay)
            
            raise ImageGenerationError(
                message="Retry mechanism failed",
                generation_step="retry",
                context=context,
                details={"max_attempts": max_attempts}
            )
        return wrapper
    return decorator

@with_retry(
    max_attempts=3,
    retry_delay=2.0,
    backoff_factor=2.0
)
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
    
    Args:
        client: OpenAI client instance
        model: DALL-E model version
        prompt: Image generation prompt
        size: Image size (default: 1024x1024)
        quality: Image quality (default: standard)
        n: Number of images to generate (default: 1)
        style: Optional style modifier
        
    Returns:
        Generated image URL
        
    Raises:
        ImageGenerationError: When image generation fails
        ImageProcessingError: When processing response fails
    """
    context = ErrorContext(
        source="image_generation.call_openai_image_api",
        severity=ErrorSeverity.ERROR
    )
    
    try:
        # Add style to prompt if provided
        if style:
            prompt = f"{prompt}, {style} style"

        # Call OpenAI API
        response = await client.images.generate(
            model=model,
            prompt=prompt,
            size=size,
            quality=quality,
            n=n
        )

        # Extract URL from response
        try:
            if isinstance(response, dict):
                # Handle dictionary response (from mock)
                if "data" in response and isinstance(response["data"], list) and len(response["data"]) > 0:
                    image_url = response["data"][0]["url"]
                else:
                    raise ImageProcessingError(
                        message="Invalid response format from image API",
                        operation="response_parsing",
                        image_format="url",
                        context=context,
                        details={"error": "Response data is missing or malformed"}
                    )
            else:
                # Handle OpenAI response object
                image_url = response.data[0].url

            return image_url

        except Exception as e:
            logger.error(f"Error extracting URL from OpenAI response: {str(e)}")
            raise ImageProcessingError(
                message="Failed to extract image URL from response",
                operation="url_extraction",
                image_format="url",
                context=context,
                details={"error": str(e)}
            )

    except Exception as e:
        logger.error(f"Error calling OpenAI image API: {str(e)}")
        raise ImageGenerationError(
            message="Failed to generate image",
            generation_step="api_call",
            context=context,
            details={"error": str(e)}
        )

async def generate_character_images(
    client: AsyncOpenAI,
    character_name: str,
    character_traits: list,
    dalle_version: str = "dall-e-3",
    progress_callback: Callable[[int, str], None] = None
) -> List[str]:
    """
    Generate 2 different character images using DALL-E.
    
    Args:
        client: OpenAI client instance
        character_name: Name of the character
        character_traits: List of character traits
        dalle_version: The DALL-E version to use ('dall-e-2' or 'dall-e-3')
        progress_callback: Optional callback function to report progress and new images
    
    Returns:
        List of 2 generated image URLs
        
    Raises:
        ImageGenerationError: When image generation fails
        ImageValidationError: When input validation fails
    """
    # Validate inputs
    context = ErrorContext(
        source="image_generation.generate_character_images",
        severity=ErrorSeverity.ERROR
    )
    
    if not character_name or not isinstance(character_name, str):
        raise ImageValidationError(
            message="Invalid character name",
            validation_type="input",
            issue="character_name",
            context=context,
            details={"provided": character_name}
        )
    
    if not character_traits or not isinstance(character_traits, list):
        raise ImageValidationError(
            message="Invalid character traits",
            validation_type="input",
            issue="character_traits",
            context=context,
            details={"provided": character_traits}
        )
    
    if dalle_version not in ["dall-e-2", "dall-e-3"]:
        raise ImageValidationError(
            message="Invalid DALL-E version",
            validation_type="input",
            issue="dalle_version",
            context=context,
            details={
                "provided": dalle_version,
                "valid_versions": ["dall-e-2", "dall-e-3"]
            }
        )
    
    prompt = f"""A {', '.join(character_traits)} {character_name}, illustrated in a fun and cartoonish style. Coloured, on PURE WHITE background"""
    
    logger.info(f"Generating images for character: {character_name}")
    logger.info(f"Using prompt: {prompt}")
    logger.info(f"Using DALL-E version: {dalle_version}")
    
    # Generate 2 variations of the character with delay between requests
    images = []
    for i in range(2):
        logger.info(f"Generating image {i+1}/2...")
        try:
            image_url = await call_openai_image_api(
                client=client,
                model=dalle_version,
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
                style="natural"
            )
            logger.info(f"Successfully generated image {i+1}")
            images.append(image_url)
            
            # Report progress and new image
            if progress_callback:
                progress_callback(i + 1, image_url)
            
        except (ImageGenerationError, ImageProcessingError) as e:
            # Re-raise with additional context
            e.context.source = "image_generation.generate_character_images"
            raise
        except Exception as e:
            logger.error(f"Error generating image {i+1}: {str(e)}")
            raise ImageGenerationError(
                message="Failed to generate character image",
                generation_step="character_image",
                context=context,
                details={
                    "error": str(e),
                    "image_number": i + 1
                }
            )
    
    logger.info(f"Successfully generated all {len(images)} images")
    return images

@with_retry(max_attempts=2, retry_delay=5.0)
@openai_circuit_breaker
async def generate_story_page_images(
    client: AsyncOpenAI,
    story_content: dict,
    character_name: str,
    character_traits: list
) -> List[dict]:
    """
    Generate 2 images for each page of the story using DALL-E.
    
    Args:
        client: OpenAI client instance
        story_content: Dictionary containing the story content
        character_name: Name of the main character
        character_traits: List of character traits
    
    Returns:
        List of dictionaries containing page numbers and generated image URLs
        
    Raises:
        ImageGenerationError: When image generation fails
        ImageValidationError: When input validation fails
    """
    # Validate inputs
    context = ErrorContext(
        source="image_generation.generate_story_page_images",
        severity=ErrorSeverity.ERROR
    )
    
    if not isinstance(story_content, dict) or "pages" not in story_content:
        raise ImageValidationError(
            message="Invalid story content",
            validation_type="input",
            issue="story_content",
            context=context,
            details={"error": "Story content must be a dictionary with 'pages' key"}
        )
    
    page_images = []
    
    for page in story_content["pages"]:
        if not isinstance(page, dict) or "visual_description" not in page or "page_number" not in page:
            raise ImageValidationError(
                message="Invalid page content",
                validation_type="input",
                issue="page_content",
                context=context,
                details={
                    "error": "Page must contain 'visual_description' and 'page_number'",
                    "page": page
                }
            )
        
        prompt = f"""
        Create a child-friendly illustration for a children's book page.
        Main Character: {character_name} (Traits: {', '.join(character_traits)})
        Scene Description: {page['visual_description']}
        
        Requirements:
        1. Suitable for children's books
        2. Colorful and engaging
        3. Age-appropriate
        4. Clear and simple composition
        5. Consistent with the main character's design
        """
        
        logger.info(f"Generating images for page {page['page_number']}")
        
        # Generate 2 variations for each page
        page_variations = []
        for variation in range(2):
            try:
                image_url = await call_openai_image_api(
                    client=client,
                    model="dall-e-3",
                    prompt=prompt,
                    size="1024x1024",
                    quality="standard",
                    n=1,
                    style="natural"
                )
                page_variations.append(image_url)
                logger.info(f"Generated variation {variation+1} for page {page['page_number']}")
                
            except (ImageGenerationError, ImageProcessingError) as e:
                # Re-raise with additional context
                e.context.source = "image_generation.generate_story_page_images"
                e.details.update({
                    "page_number": page["page_number"],
                    "variation": variation + 1
                })
                raise
            except Exception as e:
                logger.error(f"Error generating image for page {page['page_number']}: {str(e)}")
                raise ImageGenerationError(
                    message="Failed to generate page image",
                    generation_step="page_image",
                    context=context,
                    details={
                        "error": str(e),
                        "page_number": page["page_number"],
                        "variation": variation + 1
                    }
                )
        
        page_images.append({
            "page_number": page["page_number"],
            "image_urls": page_variations
        })
    
    return page_images

@with_retry(max_attempts=2, retry_delay=2.0)
@openai_circuit_breaker
async def enhance_image_prompt(
    client: AsyncOpenAI,
    name: str,
    traits: List[str],
    base_prompt: str
) -> str:
    """
    Enhance an image generation prompt using GPT-4.
    
    Args:
        client: OpenAI client instance
        name: Character name
        traits: Character traits
        base_prompt: Base prompt to enhance
        
    Returns:
        Enhanced prompt
        
    Raises:
        ImageGenerationError: When prompt enhancement fails
    """
    context = ErrorContext(
        source="image_generation.enhance_image_prompt",
        severity=ErrorSeverity.ERROR
    )
    
    try:
        # Validate inputs
        if not all([name, traits, base_prompt]):
            raise ImageValidationError(
                message="Missing required prompt parameters",
                validation_type="input",
                issue="prompt_parameters",
                context=context,
                details={
                    "name": bool(name),
                    "traits": bool(traits),
                    "base_prompt": bool(base_prompt)
                }
            )
        
        system_prompt = """
        You are an expert at crafting detailed, child-friendly image generation prompts.
        Enhance the given prompt while maintaining:
        1. Child-appropriate content
        2. Clear visual descriptions
        3. Consistent style
        4. Character accuracy
        """
        
        user_prompt = f"""
        Character: {name}
        Traits: {', '.join(traits)}
        Base Prompt: {base_prompt}
        
        Please enhance this prompt for better image generation while keeping it child-friendly and consistent with the character.
        """
        
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )
        
        enhanced_prompt = response.choices[0].message.content.strip()
        return enhanced_prompt
        
    except Exception as e:
        logger.error(f"Error enhancing prompt: {str(e)}")
        raise ImageGenerationError(
            message="Failed to enhance image prompt",
            generation_step="prompt_enhancement",
            context=context,
            details={"error": str(e)}
        ) 