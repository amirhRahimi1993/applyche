"""
Shared security helpers for hashing and verifying passwords.
"""
from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_BCRYPT_MAX_BYTES = 72


def _ensure_within_bcrypt_limit(password: str) -> None:
    encoded = password.encode("utf-8")
    if len(encoded) > _BCRYPT_MAX_BYTES:
        raise ValueError(
            "Password exceeds bcrypt's 72-byte limit. "
            "Please use a shorter password."
        )


def hash_password(password: str) -> str:
    """Return a bcrypt hash for the given plain-text password."""
    if not password:
        raise ValueError("Password cannot be empty")
    _ensure_within_bcrypt_limit(password)
    return _pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Safely verify a password against the stored hash.
    Falls back to plain comparison if legacy data is not hashed.
    """
    if not hashed_password:
        return False

    try:
        _ensure_within_bcrypt_limit(plain_password)
        return _pwd_context.verify(plain_password, hashed_password)
    except ValueError:
        # Older rows may still store plain-text passwords.
        return plain_password == hashed_password


