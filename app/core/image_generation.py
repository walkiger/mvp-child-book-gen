"""
Image generation functionality using OpenAI's DALL-E.
"""

from typing import List, Callable
import asyncio
import logging
from openai import AsyncOpenAI

from utils.error_handling import (
    ImageError, with_retry, CircuitBreaker, setup_logger,
    BaseError
)
from utils.error_templates import (
    IMAGE_GENERATION_ERROR, 
    OPERATION_TIMEOUT,
    SERVICE_UNAVAILABLE
)

# Set up logger
logger = setup_logger("image_generation", "logs/image_generation.log")

# Circuit breaker for OpenAI API calls
openai_circuit_breaker = CircuitBreaker(
    name="OpenAI", 
    failure_threshold=3,  # 3 failures will open the circuit
    reset_timeout=300     # Wait 5 minutes before trying again
)

# Retry decorator with backoff for OpenAI API calls
@with_retry(
    max_attempts=3,
    retry_delay=2.0,
    backoff_factor=2.0,
    exceptions=(Exception,)  # Retry on all exceptions
)
@openai_circuit_breaker
async def call_openai_image_api(client, model, prompt, size, quality, n, style):
    """
    Call the OpenAI image generation API with circuit breaker and retry logic.
    
    Args:
        client: OpenAI client
        model: DALL-E model version
        prompt: Image generation prompt
        size: Image size
        quality: Image quality
        n: Number of images to generate
        style: Image style
        
    Returns:
        OpenAI API response
        
    Raises:
        ImageError: If image generation fails after retries
    """
    try:
        return await client.images.generate(
            model=model,
            prompt=prompt,
            size=size,
            quality=quality,
            n=n,
            style=style
        )
    except Exception as e:
        error_message = IMAGE_GENERATION_ERROR.format(details=str(e))
        logger.error(error_message)
        raise ImageError(error_message, error_code="E-IMG-002", details=str(e))


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
        ImageError: If image generation fails
    """
    prompt = f"""A {', '.join(character_traits)} {character_name}, illustrated in a fun and cartoonish style. Coloured, on PURE WHITE background"""
    
    logger.info(f"Generating images for character: {character_name}")
    logger.info(f"Using prompt: {prompt}")
    logger.info(f"Using DALL-E version: {dalle_version}")
    
    # Generate 2 variations of the character with delay between requests
    images = []
    for i in range(2):
        logger.info(f"Generating image {i+1}/2...")
        try:
            response = await call_openai_image_api(
                client=client,
                model=dalle_version,
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
                style="natural"
            )
            logger.info(f"Successfully generated image {i+1}")
            image_url = response.data[0].url
            images.append(image_url)
            
            # Report progress and new image
            if progress_callback:
                progress_callback(i + 1, image_url)
            
        except BaseError as e:
            # Re-raise BaseError subclasses directly
            raise
        except Exception as e:
            error_message = IMAGE_GENERATION_ERROR.format(details=str(e))
            logger.error(f"Error generating image {i+1}: {str(e)}")
            raise ImageError(
                message=error_message,
                error_code="E-IMG-001",
                details=str(e)
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
        ImageError: If image generation fails
    """
    page_images = []
    
    for page in story_content["pages"]:
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
                response = await call_openai_image_api(
                    client=client,
                    model="dall-e-3",
                    prompt=prompt,
                    size="1024x1024",
                    quality="standard",
                    n=1,
                    style="natural"
                )
                page_variations.append(response.data[0].url)
                logger.info(f"Generated variation {variation+1} for page {page['page_number']}")
                
            except BaseError as e:
                # Re-raise BaseError subclasses directly
                raise
            except Exception as e:
                error_message = IMAGE_GENERATION_ERROR.format(details=str(e))
                logger.error(f"Error generating image for page {page['page_number']}: {str(e)}")
                raise ImageError(
                    message=error_message,
                    error_code="E-IMG-003",
                    details=str(e)
                )
        
        page_images.append({
            "page_number": page["page_number"],
            "image_urls": page_variations
        })
    
    return page_images 