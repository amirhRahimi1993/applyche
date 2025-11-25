# ApplyChe FastAPI Backend

This FastAPI application provides REST API endpoints to connect the PyQt6 `main_ui.py` application to the PostgreSQL database.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure your database connection settings are correct in `model/server_info.env`:
```
DB_USER=postgres
DB_PASS=applyche
DB_HOST=localhost
DB_PORT=5434
DB_NAME=applyche_global
```

**Database Configuration:**
- **PostgreSQL Version**: 18 (recommended)
- **Default Port**: 5434 (PostgreSQL 18 default)
- **Default Host**: localhost
- **Default User**: postgres
- **Default Password**: applyche

**For Remote Server:**
To connect to a remote PostgreSQL server, update `model/server_info.env`:
```
DB_USER=your_username
DB_PASS=your_password
DB_HOST=your_server_ip_or_domain
DB_PORT=5432
DB_NAME=applyche_global
```

All database connection files automatically read from this configuration file with sensible defaults.

3. Start the FastAPI server:
```bash
python -m api.main
```

Or using uvicorn directly:
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Dashboard
- `GET /api/dashboard/stats/{user_email}` - Get dashboard statistics
- `GET /api/dashboard/email-analysis/{user_email}?email_type={type}` - Get email analysis

### Email Templates
- `POST /api/email-templates/` - Create email template
- `GET /api/email-templates/{user_email}` - Get all templates for user
- `GET /api/email-templates/{user_email}/{template_id}` - Get specific template
- `PUT /api/email-templates/{template_id}` - Update template
- `DELETE /api/email-templates/{template_id}` - Delete template

### Sending Rules
- `POST /api/sending-rules/` - Create/update sending rules
- `GET /api/sending-rules/{user_email}` - Get sending rules
- `PATCH /api/sending-rules/{user_email}` - Partially update rules

### Email Queue
- `POST /api/email-queue/` - Add email to queue
- `GET /api/email-queue/{user_email}` - Get queue items
- `PATCH /api/email-queue/{queue_id}/status` - Update queue status
- `GET /api/email-queue/logs/{user_email}` - Get send logs

## Using the API Client

The `api_client.py` module provides a Python client for interacting with the API:

```python
from api_client import ApplyCheAPIClient

client = ApplyCheAPIClient("http://localhost:8000")

# Get dashboard stats
stats = client.get_dashboard_stats("user@example.com")

# Create email template
template = client.create_email_template(
    user_email="user@example.com",
    template_body="<html>...</html>",
    template_type=0,
    subject="Hello"
)

# Get sending rules
rules = client.get_sending_rules("user@example.com")
```

## Integration with main_ui.py

To use the API in `main_ui.py`, replace direct database calls with API client calls:

```python
from api_client import ApplyCheAPIClient

class Dashboard:
    def __init__(self, widget):
        self.widget = widget
        self.api_client = ApplyCheAPIClient()
    
    def __fetch_report_from_controller(self):
        user_email = "user@example.com"  # Get from session/auth
        stats = self.api_client.get_dashboard_stats(user_email)
        return stats
```

## Notes

- The API uses the same database connection settings as the existing code
- Database configuration is flexible and can be changed via `model/server_info.env`
- Default configuration: PostgreSQL 18 on localhost:5434
- CORS is enabled for all origins (restrict in production)
- All endpoints require proper error handling in the client
- The API follows RESTful conventions


