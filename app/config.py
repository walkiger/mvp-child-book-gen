# app/config.py

"""
Application configuration using Pydantic's BaseSettings.
"""

import os
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Secret key (must be set as an environment variable or in .env)
    SECRET_KEY: str = Field(..., min_length=32)

    # Database settings
    DATABASE_NAME: str = 'storybook.db'
    DATABASE_DIR: str = ''  # If empty, defaults to project root directory

    # Additional settings can be added here

    @property
    def DATABASE_PATH(self) -> str:
        """
        Construct the full path to the database file using os.path.
        """
        if self.DATABASE_DIR:
            # Use the provided directory from settings
            base_dir = self.DATABASE_DIR
        else:
            # Use the project's root directory
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

        # Ensure the base directory exists
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        # Construct the full database path
        database_path = os.path.join(base_dir, self.DATABASE_NAME)
        return database_path

    # Update configuration for Pydantic v2.x
    model_config = {
        "env_file": ".env",
    }

# Instantiate the settings
settings = Settings()
