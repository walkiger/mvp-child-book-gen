"""
Tests for the application config module.
"""
import os
import pytest
from app.config import Settings


def test_settings_initialization(monkeypatch):
    """Test that settings can be initialized with environment variables."""
    # Set environment variables for required settings
    monkeypatch.setenv("SECRET_KEY", "test_secret_key_16chars")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test_openai_key")
    
    # Initialize settings with testing flag
    settings = Settings(testing=True)
    
    # Check that the settings were loaded correctly
    assert settings.SECRET_KEY == "test_secret_key_16chars"
    assert settings.OPENAI_API_KEY == "sk-test_openai_key"
    assert settings.DATABASE_NAME == "storybook.db"
    assert settings.DATABASE_DIR == ""
    assert settings.ALGORITHM == "HS256"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30


def test_settings_with_custom_values(monkeypatch):
    """Test that settings can be initialized with custom values."""
    # Set environment variables
    monkeypatch.setenv("SECRET_KEY", "custom_secret_key_16chars")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-custom_openai_key")
    monkeypatch.setenv("DATABASE_NAME", "custom.db")
    monkeypatch.setenv("DATABASE_DIR", "/custom/dir")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    
    # Initialize settings with testing flag
    settings = Settings(testing=True)
    
    # Check that the settings were loaded correctly
    assert settings.SECRET_KEY == "custom_secret_key_16chars"
    assert settings.OPENAI_API_KEY == "sk-custom_openai_key"
    assert settings.DATABASE_NAME == "custom.db"
    assert settings.DATABASE_DIR == "/custom/dir"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 60


def test_database_path_default_directory(monkeypatch, temp_dir):
    """Test that DATABASE_PATH is constructed correctly with default directory."""
    # Set environment variables
    monkeypatch.setenv("SECRET_KEY", "test_secret_key_16chars")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test_openai_key")
    monkeypatch.setenv("DATABASE_NAME", "test.db")
    monkeypatch.setenv("DATABASE_DIR", "")  # Empty means use default directory
    
    # Initialize settings with testing flag
    settings = Settings(testing=True)
    
    # Check that the database path is constructed correctly
    assert settings.DATABASE_PATH.endswith("test.db")
    assert os.path.dirname(settings.DATABASE_PATH) != ""  # Should use a default directory


def test_database_path_custom_directory(monkeypatch, temp_dir):
    """Test that DATABASE_PATH is constructed correctly with custom directory."""
    # Set environment variables
    monkeypatch.setenv("SECRET_KEY", "test_secret_key_16chars")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test_openai_key")
    monkeypatch.setenv("DATABASE_NAME", "test.db")
    monkeypatch.setenv("DATABASE_DIR", temp_dir)
    
    # Initialize settings with testing flag
    settings = Settings(testing=True)
    
    # Check that the database path is constructed correctly
    assert settings.DATABASE_PATH == os.path.join(temp_dir, "test.db")


def test_database_url(monkeypatch, temp_dir):
    """Test that DATABASE_URL is constructed correctly."""
    # Set environment variables
    monkeypatch.setenv("SECRET_KEY", "test_secret_key_16chars")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test_openai_key")
    monkeypatch.setenv("DATABASE_NAME", "test.db")
    monkeypatch.setenv("DATABASE_DIR", temp_dir)
    
    # Initialize settings with testing flag
    settings = Settings(testing=True)
    
    # Check that the database URL is constructed correctly
    expected_path = os.path.join(temp_dir, "test.db")
    assert settings.DATABASE_URL == f"sqlite:///{expected_path}" 