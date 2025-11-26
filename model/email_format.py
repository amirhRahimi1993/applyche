"""
Utility helpers around the SQLAlchemy ORM `SendingRules` table.
Historically this module used psycopg directly; it now relies on the shared ORM session.
"""
from typing import Dict, Optional

from sqlalchemy import select

from api.database import SessionLocal
from api.db_models import SendingRules, User


class EmailFormat:
    """Lightweight helper to read/write sending rule preferences via ORM sessions."""

    def __init__(self, user_email: str):
        self.user_email = user_email
        self._session_factory = SessionLocal
        self._fields = (
            "main_mail_number",
            "reminder_one",
            "reminder_two",
            "reminder_three",
            "local_professor_time",
            "max_email_per_university",
            "send_working_day_only",
            "period_between_reminders",
            "delay_sending_mail",
            "start_time_send",
        )

    def _serialize(self, rules: SendingRules) -> Dict[str, object]:
        return {field: getattr(rules, field) for field in self._fields}

    def load_format(self) -> Optional[Dict[str, object]]:
        """Return the user's sending rules as a dictionary, or None if not configured."""
        with self._session_factory() as session:
            rules = session.execute(
                select(SendingRules).where(SendingRules.user_email == self.user_email)
            ).scalars().first()
            if not rules:
                return None
            return self._serialize(rules)

    def insert_format(self, preferences: Dict[str, object]) -> Dict[str, object]:
        """
        Create or update sending rules for the user.
        Keys in `preferences` should match the SendingRules ORM columns listed in `_fields`.
        """
        with self._session_factory() as session:
            rules = session.execute(
                select(SendingRules).where(SendingRules.user_email == self.user_email)
            ).scalars().first()

            if not rules:
                # Ensure the user row exists before creating sending rules
                user = session.get(User, self.user_email)
                if not user:
                    user = User(
                        email=self.user_email,
                        password_hash="",
                        is_active=True,
                    )
                    session.add(user)
                    session.flush()

                rules = SendingRules(user_email=self.user_email)

            for field in self._fields:
                if field in preferences:
                    setattr(rules, field, preferences[field])

            session.add(rules)
            session.commit()
            session.refresh(rules)
            return self._serialize(rules)


__all__ = ["EmailFormat"]