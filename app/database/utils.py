# app/database/utils.py

"""
Utility functions for the database, including password hashing.
"""

from datetime import datetime, UTC
from uuid import uuid4
from argon2 import PasswordHasher, exceptions as argon2_exceptions
from app.core.errors.base import ErrorContext, ErrorSeverity
from app.core.errors.auth import PasswordHashingError, PasswordVerificationError

# Initialize Argon2 password hasher with recommended parameters
pwd_hasher = PasswordHasher(
    time_cost=2,      # Number of iterations
    memory_cost=102400,  # 100MB memory usage
    parallelism=8,    # Number of parallel threads
    hash_len=32,      # Length of the hash in bytes
    salt_len=16       # Length of the random salt in bytes
)


def hash_password(password: str) -> str:
    """
    Hash a password using Argon2.

    Args:
        password (str): The plain text password.

    Returns:
        str: The hashed password.

    Raises:
        PasswordHashingError: If there's an error during password hashing.
    """
    try:
        return pwd_hasher.hash(password)
    except argon2_exceptions.HashingError as e:
        error_context = ErrorContext(
            source="utils.hash_password",
            severity=ErrorSeverity.ERROR,
            timestamp=datetime.now(UTC),
            error_id=str(uuid4()),
            additional_data={"error": str(e)}
        )
        raise PasswordHashingError(
            message="Failed to hash password",
            error_code="AUTH-HASH-001",
            context=error_context
        )
    except Exception as e:
        error_context = ErrorContext(
            source="utils.hash_password",
            severity=ErrorSeverity.ERROR,
            timestamp=datetime.now(UTC),
            error_id=str(uuid4()),
            additional_data={"error": str(e)}
        )
        raise PasswordHashingError(
            message=f"Unexpected error during password hashing: {str(e)}",
            error_code="AUTH-HASH-002",
            context=error_context
        )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password using Argon2.

    Args:
        plain_password (str): The plain text password.
        hashed_password (str): The hashed password.

    Returns:
        bool: True if the passwords match, False otherwise.

    Raises:
        PasswordVerificationError: If there's an error during password verification.
    """
    try:
        pwd_hasher.verify(hashed_password, plain_password)
        return True
    except argon2_exceptions.VerifyMismatchError:
        # This is an expected error when passwords don't match
        return False
    except argon2_exceptions.VerificationError as e:
        error_context = ErrorContext(
            source="utils.verify_password",
            severity=ErrorSeverity.ERROR,
            timestamp=datetime.now(UTC),
            error_id=str(uuid4()),
            additional_data={"error": str(e)}
        )
        raise PasswordVerificationError(
            message="Invalid hash format or corrupted hash",
            error_code="AUTH-VERIFY-001",
            context=error_context
        )
    except argon2_exceptions.InvalidHash as e:
        error_context = ErrorContext(
            source="utils.verify_password",
            severity=ErrorSeverity.ERROR,
            timestamp=datetime.now(UTC),
            error_id=str(uuid4()),
            additional_data={"error": str(e)}
        )
        raise PasswordVerificationError(
            message="Invalid hash format",
            error_code="AUTH-VERIFY-002",
            context=error_context
        )
    except Exception as e:
        error_context = ErrorContext(
            source="utils.verify_password",
            severity=ErrorSeverity.ERROR,
            timestamp=datetime.now(UTC),
            error_id=str(uuid4()),
            additional_data={"error": str(e)}
        )
        raise PasswordVerificationError(
            message=f"Unexpected error during password verification: {str(e)}",
            error_code="AUTH-VERIFY-003",
            context=error_context
        )
