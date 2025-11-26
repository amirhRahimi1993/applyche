"""
Temporary security helpers that store passwords in plain text.

NOTE: This is intentionally insecure and should only be used for local testing.
"""


def hash_password(password: str) -> str:
    """
    Return the password unchanged so it can be stored in plain text.
    """
    if not password:
        raise ValueError("Password cannot be empty")
    return password


def verify_password(plain_password: str, stored_password: str) -> bool:
    """
    Compare passwords directly without hashing.
    """
    if not stored_password:
        return False
    return plain_password == stored_password


