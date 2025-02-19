"""
SQLAlchemy models for the application, updated to include new fields and models.
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    JSON,
    Float,
    CheckConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    characters = relationship("Character", back_populates="user")
    stories = relationship("Story", back_populates="user")
    subscriptions = relationship("Subscription", back_populates="user")
    payments = relationship("Payment", back_populates="user")

class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    traits = Column(JSON)
    image_prompt = Column(String)
    image_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="characters")
    story_characters = relationship("StoryCharacter", back_populates="character")

class Story(Base):
    __tablename__ = "stories"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(JSON)
    age_group = Column(String, nullable=False)
    page_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            "age_group IN ('1-2', '3-5', '6-8', '9-12')",
            name="valid_age_groups",
        ),
    )

    user = relationship("User", back_populates="stories")
    images = relationship("Image", back_populates="story")
    story_characters = relationship("StoryCharacter", back_populates="story")

class StoryCharacter(Base):
    __tablename__ = "story_characters"

    story_id = Column(Integer, ForeignKey("stories.id"), primary_key=True)
    character_id = Column(Integer, ForeignKey("characters.id"), primary_key=True)

    story = relationship("Story", back_populates="story_characters")
    character = relationship("Character", back_populates="story_characters")

class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True)
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=True)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=True)
    image_path = Column(String, nullable=False)
    generation_cost = Column(Float, nullable=True)  # New field added
    generated_at = Column(DateTime, default=datetime.utcnow)

    story = relationship("Story", back_populates="images")
    character = relationship("Character")

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)  # 'free', 'basic', 'pro'
    price_monthly = Column(Integer)  # Price in cents
    features = Column(JSON, nullable=False)
    stripe_price_id = Column(String)  # New field added

    __table_args__ = (
        CheckConstraint(
            "name IN ('free', 'basic', 'pro')",
            name="valid_plan_names",
        ),
    )

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=False)
    status = Column(String, default="active")
    current_period_end = Column(DateTime)
    stripe_subscription_id = Column(String)  # New field added
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="subscriptions")
    plan = relationship("SubscriptionPlan")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default='EUR')
    provider = Column(String, nullable=False)  # 'stripe' or 'paypal'
    provider_payment_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="payments")
