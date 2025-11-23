"""
API Client for main_ui.py to interact with FastAPI backend
"""
import requests
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone


class ApplyCheAPIClient:
    """Client for interacting with ApplyChe FastAPI backend"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make GET request"""
        response = self.session.get(f"{self.base_url}{endpoint}", params=params)
        response.raise_for_status()
        return response.json()
    
    def _post(self, endpoint: str, data: Dict) -> Dict:
        """Make POST request"""
        response = self.session.post(f"{self.base_url}{endpoint}", json=data)
        response.raise_for_status()
        return response.json()
    
    def _put(self, endpoint: str, data: Dict) -> Dict:
        """Make PUT request"""
        response = self.session.put(f"{self.base_url}{endpoint}", json=data)
        response.raise_for_status()
        return response.json()
    
    def _patch(self, endpoint: str, data: Dict) -> Dict:
        """Make PATCH request"""
        response = self.session.patch(f"{self.base_url}{endpoint}", json=data)
        response.raise_for_status()
        return response.json()
    
    def _delete(self, endpoint: str) -> Dict:
        """Make DELETE request"""
        response = self.session.delete(f"{self.base_url}{endpoint}")
        response.raise_for_status()
        return response.json()
    
    # Dashboard methods
    def get_dashboard_stats(self, user_email: str) -> Dict:
        """Get dashboard statistics"""
        return self._get(f"/api/dashboard/stats/{user_email}")
    
    def get_email_analysis(self, user_email: str, email_type: str) -> Dict:
        """Get email analysis by type"""
        return self._get(f"/api/dashboard/email-analysis/{user_email}", params={"email_type": email_type})
    
    # Email Template methods
    def create_email_template(self, user_email: str, template_body: str, 
                             template_type: int, subject: Optional[str] = None,
                             file_paths: Optional[List[str]] = None) -> Dict:
        """Create email template with optional file paths"""
        # Build URL with query parameters for file_paths
        url = f"{self.base_url}/api/email-templates/"
        if file_paths:
            # FastAPI expects query parameters as repeated keys for lists
            from urllib.parse import urlencode
            params_list = [("file_paths", fp) for fp in file_paths]
            url += "?" + urlencode(params_list)
        
        response = self.session.post(
            url,
            json={
                "user_email": user_email,
                "template_body": template_body,
                "template_type": template_type,
                "subject": subject
            }
        )
        response.raise_for_status()
        return response.json()
    
    def get_email_templates(self, user_email: str) -> List[Dict]:
        """Get all email templates for user"""
        return self._get(f"/api/email-templates/{user_email}")
    
    def get_email_template(self, user_email: str, template_id: int) -> Dict:
        """Get specific email template"""
        return self._get(f"/api/email-templates/{user_email}/{template_id}")
    
    def update_email_template(self, template_id: int, user_email: str,
                             template_body: Optional[str] = None,
                             template_type: Optional[int] = None,
                             subject: Optional[str] = None,
                             file_paths: Optional[List[str]] = None) -> Dict:
        """Update email template with optional file paths"""
        data = {}
        if template_body is not None:
            data["template_body"] = template_body
        if template_type is not None:
            data["template_type"] = template_type
        if subject is not None:
            data["subject"] = subject
        
        # Build URL with query parameters
        from urllib.parse import urlencode
        params_list = [("user_email", user_email)]
        if file_paths is not None:
            params_list.extend([("file_paths", fp) for fp in file_paths])
        
        url = f"{self.base_url}/api/email-templates/{template_id}?" + urlencode(params_list)
        
        response = self.session.put(
            url,
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def get_template_by_type(self, user_email: str, template_type: int) -> Optional[Dict]:
        """Get the most recent template of a specific type for a user"""
        try:
            return self._get(f"/api/email-templates/{user_email}/by-type/{template_type}")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    def delete_email_template(self, template_id: int, user_email: str) -> Dict:
        """Delete email template"""
        return self._delete(f"/api/email-templates/{template_id}?user_email={user_email}")
    
    # Sending Rules methods
    def create_sending_rules(self, user_email: str, **kwargs) -> Dict:
        """Create or update sending rules"""
        data = {"user_email": user_email, **kwargs}
        return self._post("/api/sending-rules/", data)
    
    def get_sending_rules(self, user_email: str) -> Dict:
        """Get sending rules for user"""
        return self._get(f"/api/sending-rules/{user_email}")
    
    def update_sending_rules(self, user_email: str, **kwargs) -> Dict:
        """Partially update sending rules"""
        return self._patch(f"/api/sending-rules/{user_email}", kwargs)
    
    # Email Queue methods
    def create_email_queue_item(self, user_email: str, to_email: str, body: str,
                                subject: Optional[str] = None, template_id: Optional[int] = None,
                                scheduled_at: Optional[datetime] = None) -> Dict:
        """Add email to queue"""
        if scheduled_at is None:
            scheduled_at = datetime.now(timezone.utc)
        
        return self._post("/api/email-queue/", {
            "user_email": user_email,
            "to_email": to_email,
            "subject": subject,
            "body": body,
            "template_id": template_id,
            "scheduled_at": scheduled_at.isoformat() if isinstance(scheduled_at, datetime) else scheduled_at
        })
    
    def get_email_queue(self, user_email: str, status: Optional[int] = None, limit: int = 100) -> List[Dict]:
        """Get email queue items"""
        params = {"limit": limit}
        if status is not None:
            params["status"] = status
        return self._get(f"/api/email-queue/{user_email}", params=params)
    
    def update_queue_status(self, queue_id: int, status: int, user_email: str) -> Dict:
        """Update queue item status"""
        return self._patch(f"/api/email-queue/{queue_id}/status?status={status}&user_email={user_email}", {})
    
    def get_send_logs(self, user_email: str, limit: int = 100, send_type: Optional[int] = None) -> List[Dict]:
        """Get send logs"""
        params = {"limit": limit}
        if send_type is not None:
            params["send_type"] = send_type
        return self._get(f"/api/email-queue/logs/{user_email}", params=params)
    
    # Health check
    def health_check(self) -> Dict:
        """Check API health"""
        return self._get("/health")


# Example usage
if __name__ == "__main__":
    client = ApplyCheAPIClient()
    
    # Test health check
    try:
        health = client.health_check()
        print("API Health:", health)
    except Exception as e:
        print(f"API not available: {e}")

