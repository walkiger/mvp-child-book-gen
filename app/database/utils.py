"""
Utility functions for the database, including password hashing.
"""

import bcrypt

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password (str): The plain text password.

    Returns:
        str: The hashed password.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password.

    Args:
        plain_password (str): The plain text password.
        hashed_password (str): The hashed password.

    Returns:
        bool: True if the passwords match, False otherwise.
    """
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
