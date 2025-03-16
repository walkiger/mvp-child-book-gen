"""
Tests for the authentication functionality.
"""
import pytest
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from jose import jwt

from app.core.auth import create_access_token, verify_password, get_password_hash, get_current_user
from app.api.auth import register, login, oauth2_scheme
from app.api.dependencies import get_current_user as dep_get_current_user
from app.config import settings
from app.database.models import User


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
        # Test data
        data = {"sub": "test@example.com"}
        expires_delta = timedelta(minutes=15)
        
        # Create token
        token = create_access_token(data, expires_delta)
        
        # Verify the token is a string and not empty
        assert isinstance(token, str)
        assert token
        
        # Decode and verify token contents
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        assert payload["sub"] == "test@example.com"
        
        # Verify expiration was set correctly (approximately)
        exp_time = datetime.fromtimestamp(payload["exp"])
        now = datetime.utcnow()
        # Allow for a small time difference due to execution time
        assert (exp_time - now).total_seconds() > 14 * 60  # At least 14 minutes remaining
    
    def test_create_access_token_default_expiry(self):
        """Test creation of JWT access tokens with default expiry."""
        # Test data
        data = {"sub": "test@example.com"}
        
        # Create token with default expiry
        token = create_access_token(data)
        
        # Verify the token is a string and not empty
        assert isinstance(token, str)
        assert token
        
        # Decode and verify token contents
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        assert payload["sub"] == "test@example.com"
        
        # Verify expiration exists
        assert "exp" in payload


class TestAuthAPI:
    @pytest.mark.asyncio
    async def test_register_success(self):
        """Test successful user registration."""
        # Mock database and objects
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Mock user data
        user_data = MagicMock()
        user_data.email = "new@example.com"
        user_data.username = "newuser"
        user_data.password = "password123"
        user_data.first_name = "New"
        user_data.last_name = "User"
        
        with patch('app.api.auth.get_password_hash', return_value="hashed_password"), \
             patch('app.api.auth.create_access_token', return_value="test_access_token"):
            # Call the register function
            result = await register(user_data, mock_db)
        
        # Verify the function worked as expected
        assert result["access_token"] == "test_access_token"
        assert result["token_type"] == "bearer"
        
        # Verify user was added to database
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email(self):
        """Test registration with duplicate email."""
        # Mock database and existing user
        mock_db = MagicMock()
        existing_user = User(email="existing@example.com")
        mock_db.query.return_value.filter.return_value.first.return_value = existing_user
        
        # Mock user data
        user_data = MagicMock()
        user_data.email = "existing@example.com"
        
        # Call the register function - should raise exception
        with pytest.raises(HTTPException) as excinfo:
            await register(user_data, mock_db)
        
        # Verify the exception
        assert excinfo.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already registered" in excinfo.value.detail
    
    @pytest.mark.asyncio
    async def test_login_success(self):
        """Test successful login."""
        # Mock user
        mock_user = MagicMock()
        mock_user.email = "user@example.com"
        mock_user.password_hash = "hashed_password"
        
        # Mock database
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        with patch('app.api.auth.verify_password', return_value=True), \
             patch('app.api.auth.create_access_token', return_value="test_access_token"):
            # Test data
            form_data = OAuth2PasswordRequestForm(username="user@example.com", password="password123", scope="")
            
            # Call the login function
            result = await login(form_data, mock_db)
        
        # Verify the function worked as expected
        assert result["access_token"] == "test_access_token"
        assert result["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_user_not_found(self):
        """Test login with non-existent user."""
        # Mock database - no user found
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Test data
        form_data = OAuth2PasswordRequestForm(username="nonexistent@example.com", password="password", scope="")
        
        # Call the login function - should raise exception
        with pytest.raises(HTTPException) as excinfo:
            await login(form_data, mock_db)
        
        # Verify the exception
        assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect email or password" in excinfo.value.detail
    
    @pytest.mark.asyncio
    async def test_login_incorrect_password(self):
        """Test login with incorrect password."""
        # Mock user
        mock_user = MagicMock()
        mock_user.email = "user@example.com"
        mock_user.password_hash = "hashed_password"
        
        # Mock database
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        with patch('app.api.auth.verify_password', return_value=False):
            # Test data
            form_data = OAuth2PasswordRequestForm(username="user@example.com", password="wrongpassword", scope="")
            
            # Call the login function - should raise exception
            with pytest.raises(HTTPException) as excinfo:
                await login(form_data, mock_db)
        
        # Verify the exception
        assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect email or password" in excinfo.value.detail


class TestDependencies:
    def test_get_db(self):
        """Test get_db dependency yields a database session."""
        from app.api.dependencies import get_db
        
        # Create a generator from the dependency
        db_gen = get_db()
        
        # Get the yielded session (first yield)
        db = next(db_gen)
        
        # Verify we got a session-like object
        assert hasattr(db, 'close')
        
        # Try to close the generator - should not raise exceptions
        try:
            # This should trigger the finally block
            db_gen.close()
        except Exception as e:
            pytest.fail(f"get_db generator failed to close properly: {e}")
    
    def test_get_current_user_success(self):
        """Test get_current_user dependency with valid token."""
        # Mock JWT decode
        mock_jwt_decode = MagicMock(return_value={"sub": "user@example.com"})
        
        # Mock database and user
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.email = "user@example.com"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        with patch('app.api.dependencies.jwt.decode', mock_jwt_decode):
            # Call the function
            result = dep_get_current_user("valid_token", mock_db)
        
        # Verify result
        assert result == mock_user
    
    def test_get_current_user_invalid_token(self):
        """Test get_current_user dependency with invalid token."""
        with patch('app.api.dependencies.jwt.decode', side_effect=jwt.JWTError()):
            # Call the function - should raise exception
            with pytest.raises(HTTPException) as excinfo:
                dep_get_current_user("invalid_token", MagicMock())
        
        # Verify the exception
        assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in excinfo.value.detail
    
    def test_get_current_user_user_not_found(self):
        """Test get_current_user dependency with valid token but non-existent user."""
        # Mock JWT decode
        mock_jwt_decode = MagicMock(return_value={"sub": "nonexistent@example.com"})
        
        # Mock database - no user found
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with patch('app.api.dependencies.jwt.decode', mock_jwt_decode):
            # Call the function - should raise exception
            with pytest.raises(HTTPException) as excinfo:
                dep_get_current_user("valid_token", mock_db)
        
        # Verify the exception
        assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in excinfo.value.detail 