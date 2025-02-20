# app/config.py

"""
Application configuration using Pydantic's BaseSettings.
"""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Settings class to manage application configuration.
    Loads variables from the environment or a .env file.
    """

    # Secret key for application security
    SECRET_KEY: str

    # Database configuration
    DATABASE_NAME: str = 'storybook.db'
    DATABASE_DIR: str = ''  # If empty, defaults to project root directory

    # Google OAuth2 Configuration
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    # Facebook OAuth2 Configuration
    FACEBOOK_APP_ID: str
    FACEBOOK_APP_SECRET: str
    FACEBOOK_REDIRECT_URI: str

    # Microsoft OAuth2 Configuration
    MICROSOFT_CLIENT_ID: str
    MICROSOFT_CLIENT_SECRET: str
    MICROSOFT_TENANT_ID: str = 'common'
    MICROSOFT_REDIRECT_URI: str

    # Twilio Configuration for Phone Number Authentication
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_VERIFY_SERVICE_SID: str

    # Update configuration for Pydantic v2.x
    model_config = {
        "env_file": ".env",
    }

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
        os.makedirs(base_dir, exist_ok=True)

        # Construct the full database path
        database_path = os.path.join(base_dir, self.DATABASE_NAME)
        return database_path


# Instantiate the settings object
settings = Settings()
