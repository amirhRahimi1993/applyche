"""
Legacy compatibility helpers that now proxy to the SQLAlchemy ORM session.
Use `session_scope()` to work with the database safely.
"""
from contextlib import contextmanager
from typing import Generator

from api.database import SessionLocal


class ORMDatabaseConnection:
    """Wraps the global SQLAlchemy session factory for legacy callers."""

    def __init__(self):
        self._session_factory = SessionLocal

    def connect(self):
        """Maintains compatibility with older code that expected `.connect()`."""
        return self._session_factory()

    @contextmanager
    def session_scope(self) -> Generator:
        """Provide a transactional scope around a series of operations."""
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


_ORM_DB = ORMDatabaseConnection()


def connect_to_db() -> ORMDatabaseConnection:
    """
    Legacy entrypoint.
    Returns a singleton that can open ORM sessions via `.connect()` or `.session_scope()`.
    """
    return _ORM_DB