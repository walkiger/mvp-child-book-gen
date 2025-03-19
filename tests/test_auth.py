"""
Tests for the authentication functionality with unified error handling.
"""
import pytest
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, UTC
import jwt
from jwt.exceptions import PyJWTError
from jose import jwt
from app.config import Settings
from app.core.auth import (
    create_access_token,
    get_password_hash,
    verify_password,
    authenticate_user,
    register_user,
    get_current_user,
    validate_token
)
from app.api.auth import register, login, oauth2_scheme
from app.api.dependencies import get_current_user as dep_get_current_user
from app.database.models import User
from app.core.errors.base import ErrorContext, ErrorSeverity
from app.core.errors.auth import (
    AuthenticationError,
    RegistrationError,
    TokenError,
    UserNotFoundError,
    InvalidCredentialsError,
    TokenExpiredError,
    TokenValidationError,
    PasswordValidationError
)
from app.database.session import get_db
from tests.conftest import get_test_settings, generate_unique_email, generate_unique_username
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import time

# Test data
TEST_USER = {
    "email": "test@example.com",
    "password": "testpassword",
    "full_name": "Test User",
}

class TestAuthUtils:
    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "testpassword123"
        
        # Hash the password
        hashed = get_password_hash(password)
        
        # Verify hashed password is not the original
        assert hashed != password
        
        # Verify the password against the hash
        assert verify_password(password, hashed)
        
        # Verify an incorrect password returns False
        assert not verify_password("wrongpassword", hashed)
    
    def test_create_access_token(self):
        """Test creation of JWT access tokens."""
        settings = get_test_settings()
        data = {"sub": "test@example.com"}
        expires_delta = timedelta(minutes=15)
        
        # Create token
        token = create_access_token(data, expires_delta)
        
        # Verify the token
        assert isinstance(token, str)
        assert token
        
        # Decode and verify token contents
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert payload["sub"] == "test@example.com"
        
        # Verify expiration
        exp_time = datetime.fromtimestamp(payload["exp"], UTC)
        now = datetime.now(UTC)
        assert (exp_time - now).total_seconds() > 14 * 60
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, test_db_session: Session):
        """Test getting current user with invalid token."""
        with pytest.raises(TokenError) as exc_info:
            await get_current_user("invalid_token", test_db_session)
        
        error = exc_info.value
        assert error.error_context.error_code == "AUTH-TOK-INV-001"
        assert error.error_context.source == "auth.token"
        assert error.error_context.severity == ErrorSeverity.ERROR

    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found(self, test_db_session: Session):
        """Test getting current user when user doesn't exist."""
        access_token = create_access_token({"sub": "nonexistent@example.com"})

        with pytest.raises(UserNotFoundError) as exc_info:
            await get_current_user(access_token, test_db_session)
        
        error = exc_info.value
        assert error.error_context.error_code == "AUTH-USR-404"
        assert error.error_context.source == "auth.user"
        assert error.error_context.severity == ErrorSeverity.ERROR

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, test_db_session: Session):
        """Test authentication with wrong password."""
        email = generate_unique_email()
        user = User(
            email=email,
            username=generate_unique_username(),
            password_hash=get_password_hash("testpassword"),
            first_name="Test",
            last_name="User"
        )
        test_db_session.add(user)
        test_db_session.commit()

        with pytest.raises(InvalidCredentialsError) as exc_info:
            await authenticate_user(email, "wrongpassword", test_db_session)
        
        error = exc_info.value
        assert error.error_context.error_code == "AUTH-CRED-INV-001"
        assert error.error_context.source == "auth.credentials"
        assert error.error_context.severity == ErrorSeverity.ERROR
        assert error.error_context.additional_data.get("email") == email

    def test_password_validation_too_short(self):
        """Test password validation with too short password."""
        with pytest.raises(PasswordValidationError) as exc_info:
            password = "short"
            get_password_hash(password)  # This should validate length
        
        error = exc_info.value
        assert error.error_context.error_code == "AUTH-PWD-LEN-001"
        assert error.error_context.source == "auth.password"
        assert error.error_context.severity == ErrorSeverity.ERROR
        assert "length" in error.error_context.additional_data

    def test_password_validation_no_numbers(self):
        """Test password validation with no numbers."""
        with pytest.raises(PasswordValidationError) as exc_info:
            password = "NoNumbersHere!"
            get_password_hash(password)  # This should validate complexity
        
        error = exc_info.value
        assert error.error_context.error_code == "AUTH-PWD-CPX-001"
        assert error.error_context.source == "auth.password"
        assert error.error_context.severity == ErrorSeverity.ERROR
        assert "complexity" in error.error_context.additional_data

    def test_token_validation_expired(self):
        """Test validation of expired token."""
        settings = get_test_settings()
        data = {"sub": "test@example.com"}
        expires_delta = timedelta(seconds=1)
        
        # Create token that expires in 1 second
        token = create_access_token(data, expires_delta)
        
        # Wait for token to expire
        time.sleep(2)
        
        with pytest.raises(TokenExpiredError) as exc_info:
            validate_token(token)
        
        error = exc_info.value
        assert error.error_context.error_code == "AUTH-TOK-EXP-001"
        assert error.error_context.source == "auth.token"
        assert error.error_context.severity == ErrorSeverity.ERROR
        assert "exp" in error.error_context.additional_data

    def test_token_validation_invalid_signature(self):
        """Test validation of token with invalid signature."""
        settings = get_test_settings()
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        
        # Tamper with the token
        tampered_token = token[:-1] + ("1" if token[-1] == "0" else "0")
        
        with pytest.raises(TokenValidationError) as exc_info:
            validate_token(tampered_token)
        
        error = exc_info.value
        assert error.error_context.error_code == "AUTH-TOK-SIG-001"
        assert error.error_context.source == "auth.token"
        assert error.error_context.severity == ErrorSeverity.ERROR


class TestAuthAPI:
    @pytest.mark.asyncio
    async def test_register_duplicate_email(self):
        """Test registration with duplicate email."""
        mock_db = MagicMock()
        email = generate_unique_email()
        existing_user = User(email=email)
        mock_db.query.return_value.filter.return_value.first.return_value = existing_user
        
        user_data = MagicMock()
        user_data.email = email
        
        with pytest.raises(RegistrationError) as exc_info:
            await register(user_data, mock_db)
        
        error = exc_info.value
        assert error.error_context.error_code == "AUTH-REG-DUP-001"
        assert error.error_context.source == "auth.registration"
        assert error.error_context.severity == ErrorSeverity.ERROR
        assert error.error_context.additional_data.get("email") == email
    
    @pytest.mark.asyncio
    async def test_login_incorrect_password(self):
        """Test login with incorrect password."""
        email = generate_unique_email()
        mock_user = MagicMock()
        mock_user.email = email
        mock_user.password_hash = get_password_hash("correctpassword")
        
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        form_data = OAuth2PasswordRequestForm(
            username=email,
            password="wrongpassword",
            scope=""
        )
        
        with pytest.raises(InvalidCredentialsError) as exc_info:
            await login(form_data, mock_db)
        
        error = exc_info.value
        assert error.error_context.error_code == "AUTH-CRED-INV-001"
        assert error.error_context.source == "auth.login"
        assert error.error_context.severity == ErrorSeverity.ERROR
        assert error.error_context.additional_data.get("email") == email

    @pytest.mark.asyncio
    async def test_register_database_error(self):
        """Test registration with database error."""
        mock_db = MagicMock()
        mock_db.add.side_effect = SQLAlchemyError("Database error")
        
        user_data = MagicMock()
        user_data.email = generate_unique_email()
        user_data.password = "ValidPassword123!"
        
        with pytest.raises(RegistrationError) as exc_info:
            await register(user_data, mock_db)
        
        error = exc_info.value
        assert error.error_context.error_code == "AUTH-REG-DB-001"
        assert error.error_context.source == "auth.registration"
        assert error.error_context.severity == ErrorSeverity.ERROR
        assert error.error_context.additional_data.get("email") == user_data.email

    @pytest.mark.asyncio
    async def test_login_rate_limit_exceeded(self):
        """Test login with rate limit exceeded."""
        email = generate_unique_email()
        mock_user = MagicMock()
        mock_user.email = email
        mock_user.password_hash = get_password_hash("correctpassword")
        mock_user.failed_login_attempts = 5
        mock_user.last_failed_login = datetime.now(UTC) - timedelta(minutes=5)
        
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        form_data = OAuth2PasswordRequestForm(
            username=email,
            password="wrongpassword",
            scope=""
        )
        
        with pytest.raises(AuthenticationError) as exc_info:
            await login(form_data, mock_db)
        
        error = exc_info.value
        assert error.error_context.error_code == "AUTH-RATE-LIM-001"
        assert error.error_context.source == "auth.login"
        assert error.error_context.severity == ErrorSeverity.ERROR
        assert error.error_context.additional_data.get("email") == email
        assert "retry_after" in error.error_context.additional_data


class TestDependencies:
    def test_get_current_user_invalid_token(self):
        """Test get_current_user dependency with invalid token."""
        with pytest.raises(TokenError) as exc_info:
            dep_get_current_user("invalid_token")
        
        error = exc_info.value
        assert error.error_context.error_code == "AUTH-TOK-INV-001"
        assert error.error_context.source == "auth.dependencies"
        assert error.error_context.severity == ErrorSeverity.ERROR

    def test_get_current_user_user_not_found(self):
        """Test get_current_user dependency with non-existent user."""
        access_token = create_access_token({"sub": "nonexistent@example.com"})
        
        with pytest.raises(UserNotFoundError) as exc_info:
            dep_get_current_user(access_token)
        
        error = exc_info.value
        assert error.error_context.error_code == "AUTH-USR-404"
        assert error.error_context.source == "auth.dependencies"
        assert error.error_context.severity == ErrorSeverity.ERROR

    def test_get_current_user_database_error(self):
        """Test get_current_user dependency with database error."""
        access_token = create_access_token({"sub": "test@example.com"})
        
        with patch('app.api.dependencies.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_db.query.side_effect = SQLAlchemyError("Database error")
            mock_get_db.return_value = mock_db
            
            with pytest.raises(AuthenticationError) as exc_info:
                dep_get_current_user(access_token)
            
            error = exc_info.value
            assert error.error_context.error_code == "AUTH-DB-ERR-001"
            assert error.error_context.source == "auth.dependencies"
            assert error.error_context.severity == ErrorSeverity.ERROR

    def test_get_current_user_inactive_user(self):
        """Test get_current_user dependency with inactive user."""
        email = "inactive@example.com"
        access_token = create_access_token({"sub": email})
        
        with patch('app.api.dependencies.get_db') as mock_get_db:
            mock_user = MagicMock()
            mock_user.email = email
            mock_user.is_active = False
            
            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = mock_user
            mock_get_db.return_value = mock_db
            
            with pytest.raises(AuthenticationError) as exc_info:
                dep_get_current_user(access_token)
            
            error = exc_info.value
            assert error.error_context.error_code == "AUTH-USR-INACT-001"
            assert error.error_context.source == "auth.dependencies"
            assert error.error_context.severity == ErrorSeverity.ERROR
            assert error.error_context.additional_data.get("email") == email

# Add more test cases for other error scenarios...

if __name__ == "__main__":
    pytest.main(["-v", __file__]) 