"""
Shared security helpers for hashing and verifying passwords.
"""
from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_BCRYPT_MAX_BYTES = 72


def _truncate_for_bcrypt(password: str) -> bytes:
    """
    bcrypt only reads the first 72 bytes; silently trim so longer inputs still work.
    """
    return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password(password: str) -> str:
    """Return a bcrypt hash for the given plain-text password."""
    if not password:
        raise ValueError("Password cannot be empty")
    return _pwd_context.hash(_truncate_for_bcrypt(password))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Safely verify a password against the stored hash.
    Falls back to plain comparison if legacy data is not hashed.
    """
    if not hashed_password:
        return False

    try:
        return _pwd_context.verify(_truncate_for_bcrypt(plain_password), hashed_password)
    except ValueError:
        # Older rows may still store plain-text passwords.
        return plain_password == hashed_password


