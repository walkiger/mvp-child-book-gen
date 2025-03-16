"""
Story generation functionality using OpenAI's GPT-4.
"""

import json
from typing import Dict, Any
from openai import AsyncOpenAI


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
    """
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
    
    # Generate the story
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
    
    # Parse and return the story content
    story_content = json.loads(response.choices[0].message.content)
    return story_content 