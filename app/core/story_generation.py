"""
Story generation functionality using OpenAI's GPT-4.
"""

import json
import logging
from typing import Dict, Any, List
from openai import AsyncOpenAI
from .errors.story import StoryGenerationError, StoryValidationError
from .errors.base import ErrorContext, ErrorSeverity

logger = logging.getLogger(__name__)

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
    """
    Generate a children's story using GPT-4.
    
    Args:
        client: OpenAI client instance
        character_name: Name of the main character
        character_traits: List of character traits
        title: Story title
        age_group: Target age group (1-2, 3-6, 6-9, 10-12)
        page_count: Number of pages in the story
        story_tone: Desired tone (whimsical, educational, adventurous, calming)
        moral_lesson: Optional moral lesson (kindness, courage, friendship, honesty, perseverance)
    
    Returns:
        Dictionary containing the generated story content
        
    Raises:
        StoryGenerationError: When story generation fails
        StoryValidationError: When generated content is invalid
    """
    # Validate inputs
    try:
        _validate_story_params(age_group, story_tone, page_count)
    except StoryValidationError:
        raise

    # Construct the prompt
    prompt = f"""
    Create a children's story with the following specifications:
    
    Title: {title}
    Main Character: {character_name} (Traits: {', '.join(character_traits)})
    Age Group: {age_group}
    Number of Pages: {page_count}
    Tone: {story_tone}
    Moral Lesson: {moral_lesson if moral_lesson else 'None'}
    
    Requirements:
    1. Use simple, age-appropriate vocabulary
    2. Keep sentences short and clear
    3. Include engaging dialogue
    4. Make the story visually descriptive for illustration
    5. Ensure the story flows naturally between pages
    6. Maintain consistent character traits throughout
    7. Include clear visual cues for illustration on each page
    
    Please generate the story in the following JSON format:
    {{
        "title": "Story Title",
        "pages": [
            {{
                "page_number": 1,
                "text": "Page content...",
                "visual_description": "Description for illustration..."
            }},
            ...
        ]
    }}
    """
    
    context = ErrorContext(
        source="story_generation.generate_story",
        severity=ErrorSeverity.ERROR
    )
    
    # Generate the story
    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional children's book author."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        raise StoryGenerationError(
            message="Failed to generate story content",
            generation_step="api_call",
            context=context,
            details={"error": str(e)}
        )
    
    # Parse and validate the story content
    try:
        if isinstance(response, dict):
            # Handle dictionary response (from mock)
            if "choices" in response and isinstance(response["choices"], list) and len(response["choices"]) > 0:
                content = response["choices"][0]["message"]["content"]
                story_content = json.loads(content)
            else:
                raise StoryGenerationError(
                    message="Invalid response format from OpenAI",
                    generation_step="response_parsing",
                    context=context,
                    details={"error": "Response choices are missing or malformed"}
                )
        else:
            # Handle OpenAI response object
            story_content = json.loads(response.choices[0].message.content)
            
        # Validate story content
        _validate_story_content(story_content)
        return story_content

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {str(e)}")
        raise StoryGenerationError(
            message="Failed to parse story content",
            generation_step="json_parsing",
            context=context,
            details={"error": str(e)}
        )
    except StoryValidationError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise StoryGenerationError(
            message="Unexpected error during story generation",
            generation_step="content_processing",
            context=context,
            details={"error": str(e)}
        )

def _validate_story_params(age_group: str, story_tone: str, page_count: int) -> None:
    """
    Validate story generation parameters.
    
    Args:
        age_group: Target age group
        story_tone: Story tone
        page_count: Number of pages
        
    Raises:
        StoryValidationError: When parameters are invalid
    """
    context = ErrorContext(
        source="story_generation._validate_story_params",
        severity=ErrorSeverity.WARNING
    )
    
    valid_age_groups = ["1-2", "3-6", "6-9", "10-12"]
    valid_tones = ["whimsical", "educational", "adventurous", "calming"]
    
    if age_group not in valid_age_groups:
        raise StoryValidationError(
            message="Invalid age group",
            content_issue="age_group",
            context=context,
            details={
                "provided": age_group,
                "valid_options": valid_age_groups
            }
        )
    
    if story_tone not in valid_tones:
        raise StoryValidationError(
            message="Invalid story tone",
            content_issue="story_tone",
            context=context,
            details={
                "provided": story_tone,
                "valid_options": valid_tones
            }
        )
    
    if not (5 <= page_count <= 30):
        raise StoryValidationError(
            message="Invalid page count",
            content_issue="page_count",
            context=context,
            details={
                "provided": page_count,
                "valid_range": "5-30 pages"
            }
        )

def _validate_story_content(content: Dict[str, Any]) -> None:
    """
    Validate generated story content.
    
    Args:
        content: Generated story content
        
    Raises:
        StoryValidationError: When content is invalid
    """
    context = ErrorContext(
        source="story_generation._validate_story_content",
        severity=ErrorSeverity.WARNING
    )
    
    if not isinstance(content, dict):
        raise StoryValidationError(
            message="Invalid story content format",
            content_issue="format",
            context=context,
            details={"error": "Content must be a dictionary"}
        )
    
    required_fields = ["title", "pages"]
    missing_fields = [field for field in required_fields if field not in content]
    if missing_fields:
        raise StoryValidationError(
            message="Missing required story fields",
            content_issue="missing_fields",
            context=context,
            details={"missing_fields": missing_fields}
        )
    
    if not isinstance(content["pages"], list) or not content["pages"]:
        raise StoryValidationError(
            message="Invalid pages format",
            content_issue="pages",
            context=context,
            details={"error": "Pages must be a non-empty list"}
        )
    
    for page in content["pages"]:
        required_page_fields = ["page_number", "text", "visual_description"]
        missing_page_fields = [field for field in required_page_fields if field not in page]
        if missing_page_fields:
            raise StoryValidationError(
                message="Missing required page fields",
                content_issue="page_fields",
                context=context,
                details={
                    "page_number": page.get("page_number", "unknown"),
                    "missing_fields": missing_page_fields
                }
            ) 

async def enhance_story_content(
    client: AsyncOpenAI,
    story: Any
) -> Dict[str, Any]:
    """
    Enhance a story's content by making it more engaging and descriptive.
    
    Args:
        client: OpenAI client instance
        story: Story object containing content to enhance
        
    Returns:
        Dictionary containing the enhanced story content
        
    Raises:
        StoryGenerationError: When story enhancement fails
        StoryValidationError: When enhanced content is invalid
    """
    context = ErrorContext(
        source="story_generation.enhance_story_content",
        severity=ErrorSeverity.ERROR
    )
    
    try:
        # Validate story content
        if not hasattr(story, 'content') or not story.content:
            raise StoryValidationError(
                message="Invalid story content",
                content_issue="missing_content",
                context=context,
                details={"error": "Story content is missing or empty"}
            )
            
        # Prepare the enhancement prompt
        system_prompt = """
        You are a professional children's book editor. Your task is to enhance a children's story by:
        1. Making the language more engaging and descriptive
        2. Adding sensory details and vivid imagery
        3. Improving dialogue and character interactions
        4. Maintaining age-appropriate vocabulary and complexity
        5. Ensuring the story flows naturally between pages
        6. Preserving the original story structure and moral lesson
        
        Return the enhanced story in the same JSON format as the input.
        """
        
        user_prompt = f"""
        Please enhance this children's story while maintaining its core elements:
        
        Original Story:
        {json.dumps(story.content, indent=2)}
        
        Age Group: {story.age_group}
        Story Tone: {story.story_tone}
        Moral Lesson: {story.moral_lesson if hasattr(story, 'moral_lesson') else 'None'}
        
        Enhance the story while keeping the same structure and number of pages.
        """
        
        # Generate enhanced content
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        # Parse and validate enhanced content
        enhanced_content = json.loads(response.choices[0].message.content)
        _validate_story_content(enhanced_content)
        
        return enhanced_content
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {str(e)}")
        raise StoryGenerationError(
            message="Failed to parse enhanced content",
            generation_step="json_parsing",
            context=context,
            details={"error": str(e)}
        )
    except StoryValidationError:
        raise
    except Exception as e:
        logger.error(f"Error enhancing story content: {str(e)}")
        raise StoryGenerationError(
            message="Failed to enhance story content",
            generation_step="enhancement",
            context=context,
            details={"error": str(e)}
        ) 