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
    assert settings.secret_key == "test_secret_key_16chars"
    assert settings.openai_api_key == "sk-test_openai_key"
    assert settings.database_name == "test.db"  # Default database name in test mode
    assert settings.database_dir == "./test_db"  # Default test database directory
    assert settings.algorithm == "HS256"
    assert settings.access_token_expire_minutes == 30
    assert settings.dalle_default_version == "dall-e-3"
    assert settings.log_level == "DEBUG"


def test_settings_with_custom_values(monkeypatch):
    """Test that settings can be initialized with custom values."""
    # Set environment variables
    test_values = {
        "SECRET_KEY": "custom_secret_key_16chars",
        "OPENAI_API_KEY": "sk-custom_openai_key",
        "DATABASE_NAME": "custom.db",
        "DATABASE_DIR": "/custom/dir",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "60",
        "ALLOWED_ORIGINS": "http://test1.com,http://test2.com",
        "UPLOAD_DIR": "custom_uploads",
        "MAX_UPLOAD_SIZE": "10485760",  # 10MB
        "CHAT_RATE_LIMIT_PER_MINUTE": "10",
        "IMAGE_RATE_LIMIT_PER_MINUTE": "5",
        "TOKEN_LIMIT_PER_MINUTE": "30000",
        "DALLE_DEFAULT_VERSION": "dall-e-2",
        "LOG_LEVEL": "INFO"
    }
    
    # Set all environment variables
    for key, value in test_values.items():
        monkeypatch.setenv(key, value)
    
    # Initialize settings with testing flag
    settings = Settings(testing=True)
    
    # Check that all settings were loaded correctly
    assert settings.secret_key == test_values["SECRET_KEY"]
    assert settings.openai_api_key == test_values["OPENAI_API_KEY"]
    assert settings.database_name == test_values["DATABASE_NAME"]
    assert settings.database_dir == test_values["DATABASE_DIR"]
    assert settings.access_token_expire_minutes == int(test_values["ACCESS_TOKEN_EXPIRE_MINUTES"])
    assert settings.allowed_origins == test_values["ALLOWED_ORIGINS"]
    assert settings.upload_dir == test_values["UPLOAD_DIR"]
    assert settings.max_upload_size == int(test_values["MAX_UPLOAD_SIZE"])
    assert settings.chat_rate_limit_per_minute == int(test_values["CHAT_RATE_LIMIT_PER_MINUTE"])
    assert settings.image_rate_limit_per_minute == int(test_values["IMAGE_RATE_LIMIT_PER_MINUTE"])
    assert settings.token_limit_per_minute == int(test_values["TOKEN_LIMIT_PER_MINUTE"])
    assert settings.dalle_default_version == test_values["DALLE_DEFAULT_VERSION"]
    assert settings.log_level == test_values["LOG_LEVEL"]


def test_database_path_default_directory(monkeypatch, temp_dir):
    """Test that database_path is constructed correctly with default directory."""
    monkeypatch.setenv("SECRET_KEY", "test_secret_key_16chars")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test_openai_key")
    monkeypatch.setenv("DATABASE_NAME", "test.db")
    monkeypatch.setenv("DATABASE_DIR", "")  # Empty means use default directory
    
    settings = Settings(testing=True)
    
    assert settings.database_path.endswith("test.db")
    assert os.path.dirname(settings.database_path) != ""


def test_database_path_custom_directory(monkeypatch, temp_dir):
    """Test that database_path is constructed correctly with custom directory."""
    monkeypatch.setenv("SECRET_KEY", "test_secret_key_16chars")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test_openai_key")
    monkeypatch.setenv("DATABASE_NAME", "test.db")
    monkeypatch.setenv("DATABASE_DIR", temp_dir)
    
    settings = Settings(testing=True)
    
    assert settings.database_path == os.path.join(temp_dir, "test.db")


def test_database_url(monkeypatch, temp_dir):
    """Test that database_url is constructed correctly."""
    monkeypatch.setenv("SECRET_KEY", "test_secret_key_16chars")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test_openai_key")
    monkeypatch.setenv("DATABASE_NAME", "test.db")
    monkeypatch.setenv("DATABASE_DIR", temp_dir)
    
    settings = Settings(testing=True)
    
    expected_path = os.path.join(temp_dir, "test.db")
    assert settings.database_url == f"sqlite:///{expected_path}"


def test_allowed_origins_list():
    """Test that allowed_origins_list property works correctly."""
    # Test single origin
    settings = Settings(
        allowed_origins="http://localhost:3000",
        testing=True
    )
    assert settings.allowed_origins_list == ["http://localhost:3000"]

    # Test multiple origins
    settings = Settings(
        allowed_origins="http://localhost:3000,http://localhost:5173,http://localhost:3001",
        testing=True
    )
    assert settings.allowed_origins_list == [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:3001"
    ]

    # Test empty origins
    settings = Settings(allowed_origins="", testing=True)
    assert settings.allowed_origins_list == []


def test_validation_skipped_in_test_mode():
    """Test that validation is skipped when testing flag is set."""
    # These would normally fail validation
    settings = Settings(
        secret_key="short",  # Too short
        openai_api_key="invalid",  # Doesn't start with sk-
        testing=True
    )
    # Should not raise any validation errors
    assert settings.secret_key == "short"
    assert settings.openai_api_key == "invalid"


def test_validation_errors():
    """Test that validation errors are raised appropriately."""
    # Test with invalid secret key (too short)
    settings = Settings(secret_key="short", testing=True)
    assert settings.secret_key == "short"  # Should not raise an error yet
    
    # Validate settings manually
    with pytest.raises(ValueError, match="SECRET_KEY is missing or too short"):
        settings.validate_settings(force=True)

    # Test with invalid OpenAI API key
    settings = Settings(
        secret_key="test_secret_key_16chars",
        openai_api_key="invalid",
        testing=True
    )
    assert settings.openai_api_key == "invalid"  # Should not raise an error yet
    
    # Validate settings manually
    with pytest.raises(ValueError, match="OPENAI_API_KEY is missing or invalid"):
        settings.validate_settings(force=True)

    # Test with invalid origin
    settings = Settings(
        secret_key="test_secret_key_16chars",
        openai_api_key="sk-test_openai_key",
        allowed_origins="invalid_url",
        testing=True
    )
    assert settings.allowed_origins == "invalid_url"  # Should not raise an error yet
    
    # Validate settings manually
    with pytest.raises(ValueError, match="Invalid origin"):
        settings.validate_settings(force=True)


def test_upload_directory_creation(temp_dir):
    """Test that upload directory is created if it doesn't exist."""
    upload_path = os.path.join(temp_dir, "test_uploads")
    
    # Ensure directory doesn't exist
    if os.path.exists(upload_path):
        os.rmdir(upload_path)
    
    settings = Settings(
        secret_key="test_secret_key_16chars",
        openai_api_key="sk-test_openai_key",
        upload_dir=upload_path,
        testing=True
    )
    
    # Directory should not be created yet
    assert not os.path.exists(upload_path)
    
    # Validate settings to trigger directory creation
    settings.validate_settings(force=True)
    
    # Now the directory should exist
    assert os.path.exists(upload_path)
    assert os.path.isdir(upload_path)


def test_case_insensitive_env_vars(monkeypatch):
    """Test that environment variables are case insensitive."""
    # Set environment variables with different cases
    test_values = {
        "secret_key": "test_secret_key_16chars",
        "OPENAI_API_KEY": "sk-test_openai_key",
        "Database_Name": "custom.db",
        "database_DIR": "/custom/dir",
        "Access_Token_Expire_Minutes": "60"
    }
    
    for key, value in test_values.items():
        monkeypatch.setenv(key, value)
    
    settings = Settings(testing=True)
    
    assert settings.secret_key == "test_secret_key_16chars"
    assert settings.openai_api_key == "sk-test_openai_key"
    assert settings.database_name == "custom.db"
    assert settings.database_dir == "/custom/dir"
    assert settings.access_token_expire_minutes == 60


def test_settings_basic():
    """Test basic settings initialization with minimal configuration."""
    os.environ['TESTING'] = '1'
    try:
        settings = Settings(
            openai_api_key="test_key",
            secret_key="test_secret_key_12345",
            algorithm="HS256",
            access_token_expire_minutes=30,
            database_name=":memory:",
            database_dir="",
            allowed_origins="http://localhost:3000",
            upload_dir="test_uploads",
            max_upload_size=5242880,  # 5MB
            chat_rate_limit_per_minute=5,
            image_rate_limit_per_minute=3,
            token_limit_per_minute=20000,
            dalle_default_version="dall-e-3",
            log_level="DEBUG",
            testing=True
        )
        
        # Basic assertions
        assert settings.openai_api_key == "test_key"
        assert settings.secret_key == "test_secret_key_12345"
        assert settings.algorithm == "HS256"
        assert settings.access_token_expire_minutes == 30
        assert settings.database_name == ":memory:"
        assert settings.database_dir == ""
        assert settings.allowed_origins == "http://localhost:3000"
        assert settings.upload_dir == "test_uploads"
        assert settings.max_upload_size == 5242880
        assert settings.chat_rate_limit_per_minute == 5
        assert settings.image_rate_limit_per_minute == 3
        assert settings.token_limit_per_minute == 20000
        assert settings.dalle_default_version == "dall-e-3"
        assert settings.log_level == "DEBUG"
        assert settings.testing is True
        
    finally:
        os.environ.pop('TESTING', None)


def test_settings_env_vars():
    """Test settings initialization from environment variables."""
    os.environ['TESTING'] = '1'
    try:
        # Set environment variables
        os.environ['SECRET_KEY'] = "test_secret_key_12345"
        os.environ['OPENAI_API_KEY'] = "sk-test_openai_key"
        os.environ['DATABASE_NAME'] = "test.db"
        os.environ['DATABASE_DIR'] = "/test/dir"
        os.environ['ALLOWED_ORIGINS'] = "http://test.com"
        os.environ['UPLOAD_DIR'] = "test_uploads"
        os.environ['MAX_UPLOAD_SIZE'] = "5242880"
        os.environ['CHAT_RATE_LIMIT_PER_MINUTE'] = "5"
        os.environ['IMAGE_RATE_LIMIT_PER_MINUTE'] = "3"
        os.environ['TOKEN_LIMIT_PER_MINUTE'] = "20000"
        os.environ['DALLE_DEFAULT_VERSION'] = "dall-e-3"
        os.environ['LOG_LEVEL'] = "DEBUG"
        
        settings = Settings()
        
        # Check that environment variables were loaded correctly
        assert settings.secret_key == "test_secret_key_12345"
        assert settings.openai_api_key == "sk-test_openai_key"
        assert settings.database_name == "test.db"
        assert settings.database_dir == "/test/dir"
        assert settings.allowed_origins == "http://test.com"
        assert settings.upload_dir == "test_uploads"
        assert settings.max_upload_size == 5242880
        assert settings.chat_rate_limit_per_minute == 5
        assert settings.image_rate_limit_per_minute == 3
        assert settings.token_limit_per_minute == 20000
        assert settings.dalle_default_version == "dall-e-3"
        assert settings.log_level == "DEBUG"
        
    finally:
        # Clean up environment variables
        os.environ.pop('TESTING', None)
        os.environ.pop('SECRET_KEY', None)
        os.environ.pop('OPENAI_API_KEY', None)
        os.environ.pop('DATABASE_NAME', None)
        os.environ.pop('DATABASE_DIR', None)
        os.environ.pop('ALLOWED_ORIGINS', None)
        os.environ.pop('UPLOAD_DIR', None)
        os.environ.pop('MAX_UPLOAD_SIZE', None)
        os.environ.pop('CHAT_RATE_LIMIT_PER_MINUTE', None)
        os.environ.pop('IMAGE_RATE_LIMIT_PER_MINUTE', None)
        os.environ.pop('TOKEN_LIMIT_PER_MINUTE', None)
        os.environ.pop('DALLE_DEFAULT_VERSION', None)
        os.environ.pop('LOG_LEVEL', None)


def test_settings_validation():
    """Test settings validation rules."""
    os.environ['TESTING'] = '1'
    try:
        # Test with invalid secret key (too short)
        settings = Settings(secret_key="short")
        assert settings.secret_key == "short"  # Should not raise an error yet
        
        # Validate settings manually
        with pytest.raises(ValueError, match="SECRET_KEY is missing or too short"):
            settings.validate_settings(force=True)
        
        # Test with invalid OpenAI API key
        settings = Settings(
            secret_key="test_secret_key_16chars",
            openai_api_key="invalid"
        )
        assert settings.openai_api_key == "invalid"  # Should not raise an error yet
        
        # Validate settings manually
        with pytest.raises(ValueError, match="OPENAI_API_KEY is missing or invalid"):
            settings.validate_settings(force=True)
        
        # Test with invalid origin
        settings = Settings(
            secret_key="test_secret_key_16chars",
            openai_api_key="sk-test_openai_key",
            allowed_origins="invalid_url"
        )
        assert settings.allowed_origins == "invalid_url"  # Should not raise an error yet
        
        # Validate settings manually
        with pytest.raises(ValueError, match="Invalid origin"):
            settings.validate_settings(force=True)
            
    finally:
        os.environ.pop('TESTING', None) 