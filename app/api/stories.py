# app/api/stories.py

"""
API endpoints for story generation with free plan enforcement.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import openai
import tiktoken
from typing import Dict, Any

from app.schemas.story import StoryCreate, StoryResponse
from app.database.models import Story, Character, User, SubscriptionPlan
from app.core.ai_utils import DEVELOPER_PROMPT, check_rate_limits, update_rate_metrics
from app.api.dependencies import get_db, get_current_user
from app.config import settings

router = APIRouter(prefix="/stories", tags=["stories"])


def get_free_plan(db: Session) -> Dict[str, Any]:
    """Get free subscription plan constraints."""
    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.name == "free"
    ).first()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Free plan configuration missing"
        )

    return plan.features  # Returns dict of free plan constraints


@router.post("/generate", response_model=StoryResponse)
async def generate_story(
        story_data: StoryCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    """
    Generate story with free plan enforcement:
    - Max 3 stories per user
    - Max 10 pages (locations) per story
    - No generated images - subject to change
    """
    openai.api_key = settings.OPENAI_API_KEY

    # Get free plan constraints
    free_plan = get_free_plan(db)

    # Enforce story limit
    story_count = db.query(Story).filter(
        Story.user_id == current_user.id
    ).count()

    if story_count >= free_plan["max_books"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Free plan limit: {free_plan['max_books']} stories max"
        )

    # Enforce pages/locations limit
    if len(story_data.locations) > free_plan["max_pages_per_story"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Free plan limit: {free_plan['max_pages_per_story']} locations max"
        )

    # Validate character ownership
    character = db.query(Character).filter(
        (Character.id == story_data.character_id) &
        (Character.user_id == current_user.id)
    ).first()

    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )

    # Enforce OpenAI rate limits
    check_rate_limits()

    # Build structured prompt
    prompt = f"""
    **Child Story Requirements (STRICT):**
    - Age Group: {story_data.age_group}
    - Character: {character.name} ({character.traits})
    - Locations: {", ".join(story_data.locations)}
    - Moral: {story_data.moral_lesson or "None"}
    - Tone: {story_data.story_tone}
    - Length: Exactly {len(story_data.locations)} pages

    - Simple vocabulary only
    - Max {free_plan['max_pages_per_story']} pages

    **Output Format (JSON):**
    {{
        "title": "Story Title",
        "pages": [
            {{
                "text": "Page content...",
                "image_prompt": null  # FREE PLAN DISABLES IMAGES
            }}
        ]
    }}
    """

    messages = [
        {"role": "system", "content": DEVELOPER_PROMPT},
        {"role": "user", "content": prompt}
    ]

    try:
        # Token calculation
        encoder = tiktoken.encoding_for_model("gpt-4o-mini")
        tokens_used = len(encoder.encode(prompt))
        update_rate_metrics(tokens_used)

        # Generate story
        response = await openai.ChatCompletion.acreate(
            model="gpt-4o-mini",
            messages=messages,
            temperature=story_data.temperature,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )

        story_content = response.choices[0].message.content

        # Save story with plan metadata
        new_story = Story(
            user_id=current_user.id,
            character_id=character.id,
            title=story_data.title,
            content=story_content,
            age_group=story_data.age_group,
            moral_lesson=story_data.moral_lesson,
            story_tone=story_data.story_tone,
            plan_used="free",
            constraints=free_plan
        )

        db.add(new_story)
        db.commit()
        db.refresh(new_story)

        return new_story

    except openai.BadRequestError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"AI model error: {e.message}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Story generation failed: {str(e)}"
        )