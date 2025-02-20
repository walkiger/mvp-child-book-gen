"""
Application configuration using Pydantic's BaseSettings.
"""

from pydantic import BaseSettings


class Settings(BaseSettings):
    """
    Settings class to manage application configuration.
    Loads variables from the environment or a .env file.
    """

    # Secret key for application security
    SECRET_KEY: str

    # Database configuration
    DATABASE_NAME: str = 'storybook.db'
    DATABASE_DIR: str = ''

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

    class Config:
        """Pydantic configuration class."""
        env_file = '.env'


# Instantiate the settings object
settings = Settings()
