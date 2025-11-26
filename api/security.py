"""
Shared security helpers for hashing and verifying passwords.
"""
from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Return a bcrypt hash for the given plain-text password."""
    if not password:
        raise ValueError("Password cannot be empty")
    return _pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Safely verify a password against the stored hash.
    Falls back to plain comparison if legacy data is not hashed.
    """
    if not hashed_password:
        return False

    try:
        return _pwd_context.verify(plain_password, hashed_password)
    except ValueError:
        # Older rows may still store plain-text passwords.
        return plain_password == hashed_password


