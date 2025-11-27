"""
Dashboard helper that now queries the PostgreSQL database exclusively via SQLAlchemy ORM.
"""
import os
from typing import Dict, Optional

from sqlalchemy import case, func

from api.database import SessionLocal
from api.db_models import EmailQueue, ProfessorContact, SendLog


class DashboardModel:
    """Expose simple helper methods for legacy UI components while using the ORM under the hood."""

    def __init__(self, default_user_email: Optional[str] = None):
        self._session_factory = SessionLocal
        self.default_user_email = default_user_email or os.getenv(
            "DEFAULT_USER_EMAIL",
            "user@example.com",
        )

    def _resolve_user(self, user_email: Optional[str]) -> str:
        return user_email or self.default_user_email

    def get_dashboard_stats(self, user_email: Optional[str] = None) -> Dict[str, int]:
        """Return the same aggregate stats exposed via the FastAPI dashboard endpoint."""
        user_email = self._resolve_user(user_email)
        with self._session_factory() as session:
            send_log_counts = session.query(
                func.sum(case((SendLog.send_type == 0, 1), else_=0)).label("main_mail"),
                func.sum(case((SendLog.send_type == 1, 1), else_=0)).label("first_reminder"),
                func.sum(case((SendLog.send_type == 2, 1), else_=0)).label("second_reminder"),
                func.sum(case((SendLog.send_type == 3, 1), else_=0)).label("third_reminder"),
            ).filter(SendLog.user_email == user_email).first()

            stats = {
                "main_mail": int(send_log_counts.main_mail or 0),
                "first_reminder": int(send_log_counts.first_reminder or 0),
                "second_reminder": int(send_log_counts.second_reminder or 0),
                "third_reminder": int(send_log_counts.third_reminder or 0),
            }

            stats["answered_professors"] = (
                session.query(func.count(ProfessorContact.id))
                .filter(
                    ProfessorContact.user_email == user_email,
                    ProfessorContact.contact_status == 3,
                )
                .scalar()
                or 0
            )

            stats["pending_queue"] = (
                session.query(func.count(EmailQueue.id))
                .filter(
                    EmailQueue.user_email == user_email,
                    EmailQueue.status == 0,
                )
                .scalar()
                or 0
            )

            return stats

    def analysis_email(self, key: str, user_email: Optional[str] = None) -> int:
        """Preserve the legacy API by returning a single metric by key."""
        stats = self.get_dashboard_stats(user_email)
        return stats.get(key, 0)

    def return_not_send_mail(self, user_email: Optional[str] = None) -> int:
        """Legacy helper retained for backwards compatibility."""
        stats = self.get_dashboard_stats(user_email)
        return stats.get("pending_queue", 0)


Dashboard = DashboardModel()
