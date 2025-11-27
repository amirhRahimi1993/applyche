"""
Thin controller wrapper that now fetches dashboard data exclusively via the ORM models.
"""
from typing import Optional

from model.dashboard_model import DashboardModel


class DashboardController:
    def __init__(self, user_email: Optional[str] = None):
        self._model = DashboardModel(default_user_email=user_email)

    def fetch_data_from_model(self, user_email: Optional[str] = None):
        return self._model.get_dashboard_stats(user_email)

    def give_data_to_view(self, user_email: Optional[str] = None):
        return self.fetch_data_from_model(user_email)

    # Legacy placeholders kept for compatibility with existing UI wiring
    def give_data_to_model(self):  # pragma: no cover - legacy hook
        return None

    def fetch_data_from_view(self):  # pragma: no cover - legacy hook
        return None