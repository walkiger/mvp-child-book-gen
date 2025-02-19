# app/database/seed.py

"""
Database initialization and seeding functions.
"""

import os
from sqlalchemy.orm import Session
from .engine import engine
from .models import Base, SubscriptionPlan
from app.config import settings

def init_db() -> None:
    """
    Initialize the database if it does not exist.
    """
    db_file = settings.DATABASE_PATH
    if not os.path.exists(db_file):
        print("Database file not found. Creating new database.")
        Base.metadata.create_all(bind=engine)
        seed_subscription_plans()
    else:
        print("Database file exists. Skipping creation.")

def seed_subscription_plans() -> None:
    """
    Seed initial subscription plans if they don't exist.
    """
    with Session(bind=engine) as db:
        if not db.query(SubscriptionPlan).first():
            free_plan = SubscriptionPlan(
                name="free",
                price_monthly=0,
                features={
                    "max_pages_per_story": 10,
                    "max_books": 3,
                    "max_images": 0,
                    "ai_access": False,
                },
            )
            basic_plan = SubscriptionPlan(
                name="basic",
                price_monthly=999,  # $9.99 in cents
                features={
                    "max_pages_per_story": 30,
                    "max_books": 10,
                    "max_images": 50,
                    "ai_access": False,
                },
            )
            pro_plan = SubscriptionPlan(
                name="pro",
                price_monthly=1999,  # $19.99 in cents
                features={
                    "max_pages_per_story": 100,
                    "max_books": 999,
                    "max_images": 200,
                    "max_images_per_generation": 10,
                    "ai_access": True,
                },
            )
            db.add_all([free_plan, basic_plan, pro_plan])
            db.commit()
            print("Subscription plans seeded.")
