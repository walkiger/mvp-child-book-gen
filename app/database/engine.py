# app/database/engine.py

"""
Database engine and session setup.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Use the DATABASE_PATH from settings
DATABASE_URL = f"sqlite:///{settings.DATABASE_PATH}"

# Initialize the database engine and session
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)
