# app/database/seed.py

"""
Database initialization and seeding.
"""

from sqlalchemy.orm import Session
from app.database.models import Base
from app.database.session import engine


def init_db() -> None:
    """
    Initialize the database by creating all tables.
    """
    Base.metadata.create_all(bind=engine)


def seed_db(db: Session) -> None:
    """
    Seed the database with initial data.
    """
    # Add any initial data seeding here if needed
    pass
