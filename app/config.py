# app/config.py

"""
Application configuration using Pydantic's BaseSettings.
"""

import os
import sys
from typing import List
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Settings class to manage application configuration.
    Loads variables from the environment or a .env file.
    """

    # Secret key for application security
    SECRET_KEY: str

    # openAI api key
    OPENAI_API_KEY: str

    # Database configuration
    DATABASE_NAME: str = 'storybook.db'
    DATABASE_DIR: str = ''  # If empty, defaults to project root directory

    # JWT Configuration
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS Configuration
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # File Upload Configuration
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB

    # Rate Limiting
    CHAT_RATE_LIMIT_PER_MINUTE: int = 5  # Chat API rate limit
    IMAGE_RATE_LIMIT_PER_MINUTE: int = 3  # Image API rate limit
    TOKEN_LIMIT_PER_MINUTE: int = 20000  # Total token limit per minute

    # Use ConfigDict instead of class-based config (fixes Pydantic deprecation warning)
    model_config = ConfigDict(
        env_file=".env",
        extra="ignore"
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print(f"Loading settings from .env file: {os.path.abspath('.env')}")
        
        # Check if we're in testing mode
        testing = kwargs.get('testing', os.environ.get('TESTING') == '1')
        
        # Validate required environment variables
        self.validate_environment(testing=testing)
        
        # Log OpenAI API key status (safely)
        print(f"OPENAI_API_KEY is set: {'Yes' if self.OPENAI_API_KEY else 'No'}")
        if self.OPENAI_API_KEY:
            print(f"OPENAI_API_KEY starts with: {self.OPENAI_API_KEY[:7]}...")

    def validate_environment(self, testing: bool = False) -> bool:
        """
        Validate that all required environment variables are set with appropriate values.
        Exits the application if critical variables are missing or invalid.
        
        Args:
            testing: If True, will not exit the application on validation errors (for tests)
        """
        validation_errors = []

        # Check for required values
        if not self.SECRET_KEY or len(self.SECRET_KEY) < 16:
            validation_errors.append("SECRET_KEY is missing or too short (should be at least 16 characters)")

        if not self.OPENAI_API_KEY or not self.OPENAI_API_KEY.startswith("sk-"):
            validation_errors.append("OPENAI_API_KEY is missing or invalid (should start with 'sk-')")


        # Validate upload directory exists or can be created
        upload_dir = self.UPLOAD_DIR
        if not os.path.exists(upload_dir):
            try:
                os.makedirs(upload_dir, exist_ok=True)
                print(f"Created upload directory: {upload_dir}")
            except Exception as e:
                validation_errors.append(f"Could not create upload directory: {str(e)}")

        # Check that allowed origins is properly formatted
        if self.ALLOWED_ORIGINS:
            try:
                # Convert comma-separated string to list
                if "," in self.ALLOWED_ORIGINS:
                    origins = [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
                else:
                    origins = [self.ALLOWED_ORIGINS.strip()]

                # Check that each origin is a valid URL
                for origin in origins:
                    if not origin.startswith(("http://", "https://")):
                        validation_errors.append(f"Invalid origin: {origin} (should start with http:// or https://)")
            except Exception as e:
                validation_errors.append(f"Error parsing ALLOWED_ORIGINS: {str(e)}")

        # Exit application if there are validation errors
        if validation_errors:
            print("ERROR: Environment validation failed:")
            for error in validation_errors:
                print(f"  - {error}")
            print("\nPlease fix these issues in your .env file and restart the application.")
            
            # Only exit if not in testing mode
            if not testing:
                sys.exit(1)
            return False
        
        print("Environment validation successful.")
        return True

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

    @property
    def DATABASE_URL(self) -> str:
        """
        Construct the SQLAlchemy database URL.
        """
        return f"sqlite:///{self.DATABASE_PATH}"
        
    @property
    def ALLOWED_ORIGINS_LIST(self) -> List[str]:
        """
        Convert the comma-separated ALLOWED_ORIGINS string to a list.
        """
        if not self.ALLOWED_ORIGINS:
            return []
        
        if "," in self.ALLOWED_ORIGINS:
            return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
        
        return [self.ALLOWED_ORIGINS.strip()]


# Create settings instance
settings = Settings()
