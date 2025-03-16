"""
SQLAlchemy models for the application.
"""

from datetime import datetime
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
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
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


class Character(Base):
    __tablename__ = 'characters'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String, nullable=False)
    traits = Column(JSON)
    image_prompt = Column(String)
    image_path = Column(String)
    generated_images = Column(JSON)  # Store array of image URLs/references
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship('User', back_populates='characters')
    stories = relationship("Story", back_populates="character")
    images = relationship("Image", back_populates="character")


class Story(Base):
    __tablename__ = 'stories'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    title = Column(String, nullable=False)
    content = Column(JSON)
    age_group = Column(String, nullable=False)
    page_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            "age_group IN ('1-2', '3-5', '6-8', '9-12')",
            name='valid_age_groups',
        ),
        CheckConstraint(
            # Allow NULL or specific values
            "moral_lesson IN ('kindness', 'courage', 'friendship', 'honesty', 'perseverance') OR moral_lesson IS NULL",
            name='valid_moral_lessons'
        ),
        CheckConstraint(
            "story_tone IN ('whimsical', 'educational', 'adventurous', 'calming')",
            name='valid_story_tones'
        )
    )

    user = relationship('User', back_populates='stories')
    images = relationship('Image', back_populates='story')
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    character = relationship("Character", back_populates="stories")
    moral_lesson = Column(String, nullable=True)
    story_tone = Column(String, nullable=False, default="whimsical")

    plan_used = Column(String, nullable=False, default="free")
    constraints = Column(JSON, nullable=False, server_default='{}')


class Image(Base):
    __tablename__ = 'images'

    id = Column(Integer, primary_key=True)
    story_id = Column(Integer, ForeignKey('stories.id'), nullable=True)
    character_id = Column(Integer, ForeignKey('characters.id'), nullable=True)
    image_data = Column(LargeBinary, nullable=False)  # Store actual image data
    image_format = Column(String, nullable=False)  # Store image format (e.g., 'png', 'jpg')
    generation_cost = Column(Float, nullable=True)
    dalle_version = Column(String, nullable=False)  # Store which DALL-E version was used
    generated_at = Column(DateTime, default=datetime.utcnow)
    regeneration_count = Column(Integer, default=0)  # Track number of regenerations
    grid_position = Column(Integer, nullable=True)  # Position in 2x2 grid (0-3)

    story = relationship('Story', back_populates='images')
    character = relationship('Character', back_populates='images')
