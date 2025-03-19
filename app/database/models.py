"""
SQLAlchemy models for the application.
"""

from datetime import datetime, UTC
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    JSON,
    Float,
    CheckConstraint,
    LargeBinary,
    Boolean,
    text
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from sqlalchemy.types import TypeDecorator

Base = declarative_base()

class UTCDateTime(TypeDecorator):
    """Automatically convert naive datetime to UTC on write and read."""
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if value.tzinfo is None:
                value = value.replace(tzinfo=UTC)
            return value.astimezone(UTC)
        return value

    def process_result_value(self, value, dialect):
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value

def utc_now():
    """Return current UTC datetime."""
    return datetime.now(UTC)

class TimestampMixin:
    """Mixin for adding created_at and updated_at columns."""
    created_at = Column(
        UTCDateTime,
        server_default=text('CURRENT_TIMESTAMP'),
        default=utc_now,
        nullable=False
    )
    updated_at = Column(
        UTCDateTime,
        server_default=text('CURRENT_TIMESTAMP'),
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )

class User(Base, TimestampMixin):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)

    characters = relationship('Character', back_populates='user')
    stories = relationship('Story', back_populates='user')
    images = relationship('Image', back_populates='user')

class Character(Base, TimestampMixin):
    __tablename__ = 'characters'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String, nullable=False)
    traits = Column(JSON)
    image_prompt = Column(String)
    image_path = Column(String)
    generated_images = Column(JSON)  # Store array of image URLs/references

    user = relationship('User', back_populates='characters')
    stories = relationship("Story", back_populates="character")
    images = relationship("Image", back_populates="character")

class Story(Base, TimestampMixin):
    __tablename__ = 'stories'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    character_id = Column(Integer, ForeignKey('characters.id'), nullable=False)
    title = Column(String, nullable=False)
    content = Column(JSON)
    age_group = Column(String, nullable=False)
    page_count = Column(Integer, default=0)
    status = Column(String, nullable=False, default="draft")
    generation_cost = Column(Float, default=0.0)
    moral_lesson = Column(String, nullable=True)
    story_tone = Column(String, nullable=False, default="whimsical")
    plan_used = Column(String, nullable=False, default="free")
    constraints = Column(JSON, nullable=False, server_default='{}')

    __table_args__ = (
        CheckConstraint(
            "age_group IN ('1-2', '3-5', '6-8', '9-12')",
            name='valid_age_groups',
        ),
        CheckConstraint(
            "moral_lesson IN ('kindness', 'courage', 'friendship', 'honesty', 'perseverance') OR moral_lesson IS NULL",
            name='valid_moral_lessons'
        ),
        CheckConstraint(
            "story_tone IN ('whimsical', 'educational', 'adventurous', 'calming')",
            name='valid_story_tones'
        ),
        CheckConstraint(
            "status IN ('draft', 'generating', 'completed', 'failed')",
            name='valid_story_status'
        )
    )

    user = relationship('User', back_populates='stories')
    images = relationship('Image', back_populates='story')
    character = relationship("Character", back_populates="stories")

class Image(Base):
    """Model for storing generated images."""
    __tablename__ = "images"

    id = Column(Integer, primary_key=True)
    data = Column(LargeBinary, nullable=False)
    format = Column(String(10), nullable=False)
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=True)  # Make nullable since character images don't have a story
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    dalle_version = Column(String(10), nullable=False, default="dall-e-3")
    generation_cost = Column(Float, nullable=False, default=0.02)
    grid_position = Column(Integer, nullable=True)  # Position in the character's image grid
    regeneration_count = Column(Integer, nullable=False, default=0)  # Track number of regenerations
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    story = relationship("Story", back_populates="images")
    character = relationship("Character", back_populates="images")
    user = relationship("User", back_populates="images")
