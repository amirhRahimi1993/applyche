# ApplyChe API - FastAPI Backend with SQLAlchemy ORM

## Overview

This project provides a RESTful API backend for the ApplyChe email management system. The API connects the PyQt6 desktop application (`main_ui.py`) to a PostgreSQL database using FastAPI and SQLAlchemy ORM.

**Python Version**: Compatible with Python 3.9+ (optimized for Python 3.12)

## What Was Created

### 1. FastAPI Application Structure

A complete FastAPI application was created to replace direct database connections in the PyQt6 application. The API provides REST endpoints for all database operations.

### 2. SQLAlchemy ORM Models

All database tables from the PostgreSQL schema (`DB/drawSQL-pgsql-export-2025-11-16.sql`) were converted to SQLAlchemy ORM models, eliminating the need for raw SQL queries.

### 3. API Routes

RESTful API endpoints were created for:
- Dashboard statistics
- Email template management
- Sending rules configuration
- Email queue management
- Send logs retrieval

## Project Structure

```
applyche/
├── api/                          # FastAPI application
│   ├── __init__.py              # Package initialization
│   ├── main.py                  # FastAPI app entry point
│   ├── database.py              # Database connection & session management
│   ├── db_models.py             # SQLAlchemy ORM models (25+ models)
│   ├── models.py                # Pydantic request/response schemas
│   └── routes/                  # API route handlers
│       ├── __init__.py
│       ├── dashboard.py         # Dashboard statistics endpoints
│       ├── email_templates.py   # Email template CRUD operations
│       ├── sending_rules.py     # Sending rules management
│       └── email_queue.py       # Email queue & send logs
│
├── DB/                          # Database schema
│   └── drawSQL-pgsql-export-2025-11-16.sql
│
├── model/                       # Original database connection (legacy)
│   ├── connect_db.py           # Original psycopg connection
│   └── server_info.env         # Database credentials
│
├── api_client.py                # Python client for API integration
├── start_api.py                 # Script to start FastAPI server
├── example_integration.py       # Examples for integrating with main_ui.py
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── DEPENDENCY_GRAPH.md          # Detailed dependency documentation
├── dependency_graph.mmd         # Mermaid diagram source
├── README_ORM.md                # ORM-specific documentation
└── MIGRATION_TO_ORM.md          # Migration guide
```

## Architecture Overview

### Component Layers

```
┌─────────────────────────────────────────┐
│      FastAPI Application (main.py)      │
│         - CORS Middleware               │
│         - Router Registration            │
└─────────────────┬───────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
┌──────────────┐      ┌──────────────┐
│   Routers    │      │   Schemas    │
│  (routes/*)  │─────▶│  (models.py) │
└──────┬───────┘      └──────────────┘
       │
       │ Depends(get_db)
       ▼
┌──────────────┐
│   Database   │
│ (database.py)│
└──────┬───────┘
       │
       │ SQLAlchemy Session
       ▼
┌──────────────┐
│  ORM Models  │
│ (db_models.py)│
└──────┬───────┘
       │
       │ SQL Queries
       ▼
┌──────────────┐
│  PostgreSQL  │
│   Database   │
└──────────────┘
```

## File Connections and Dependencies

### 1. `api/main.py` - Application Entry Point

**Purpose**: FastAPI application initialization and router registration

**Connections**:
- **Imports**: All routers from `api/routes/`
- **Registers**: All API routers with the FastAPI app
- **Configures**: CORS middleware for cross-origin requests

**Key Code**:
```python
from api.routes import dashboard, email_templates, sending_rules, email_queue

app.include_router(dashboard.router)
app.include_router(email_templates.router)
app.include_router(sending_rules.router)
app.include_router(email_queue.router)
```

### 2. `api/database.py` - Database Connection Layer

**Purpose**: Manages database connections using SQLAlchemy

**Connections**:
- **Reads**: `model/server_info.env` for database credentials
- **Creates**: SQLAlchemy engine and session factory
- **Provides**: `get_db()` dependency for FastAPI routes
- **Imports**: `Base` from `api/db_models.py` to register models

**Key Components**:
- `engine`: SQLAlchemy engine connected to PostgreSQL
- `SessionLocal`: Session factory for creating database sessions
- `get_db()`: FastAPI dependency that provides database sessions
- `get_db_session()`: Context manager for manual session management

**Usage in Routes**:
```python
from api.database import get_db
from sqlalchemy.orm import Session

@router.get("/endpoint")
async def my_endpoint(db: Session = Depends(get_db)):
    # Use db session here
    pass
```

### 3. `api/db_models.py` - ORM Models Layer

**Purpose**: SQLAlchemy ORM models representing database tables

**Connections**:
- **Extends**: `Base` from SQLAlchemy declarative_base
- **Defines**: 25+ model classes for all database tables
- **Relationships**: Foreign keys and bidirectional relationships
- **Used by**: All routers via database sessions

**Key Models**:
- `User`: Core user account model
- `EmailTemplate`: Email template storage
- `SendingRules`: Email sending configuration
- `EmailQueue`: Email queue for scheduled sending
- `SendLog`: Log of sent emails
- `ProfessorContact`: Contact tracking
- And 20+ more models...

**Example Model**:
```python
class EmailTemplate(Base):
    __tablename__ = 'email_templates'
    
    id = Column(Integer, primary_key=True)
    user_email = Column(CITEXT, ForeignKey('users.email'))
    template_body = Column(Text, nullable=False)
    # ... more columns
    
    # Relationships
    user = relationship('User', back_populates='email_templates')
```

### 4. `api/models.py` - Pydantic Schemas Layer

**Purpose**: Request/response validation schemas

**Connections**:
- **Used by**: All routers for request validation and response serialization
- **Validates**: Incoming request data
- **Serializes**: Database models to JSON responses

**Key Schemas**:
- Request schemas: `EmailTemplateCreate`, `SendingRulesCreate`, etc.
- Response schemas: `EmailTemplateResponse`, `DashboardStats`, etc.
- Update schemas: `EmailTemplateUpdate`, `SendingRulesUpdate`, etc.

**Example Schema**:
```python
class EmailTemplateCreate(BaseModel):
    user_email: EmailStr
    template_body: str
    template_type: int
    subject: Optional[str] = None
```

### 5. Router Files (`api/routes/*.py`)

**Purpose**: API endpoint handlers

**Connections**:
- **Import**: Schemas from `api/models.py`
- **Import**: ORM models from `api/db_models.py`
- **Use**: `get_db()` from `api/database.py`
- **Register**: Routes with FastAPI app via `main.py`

#### `api/routes/dashboard.py`

**Endpoints**:
- `GET /api/dashboard/stats/{user_email}` - Get dashboard statistics
- `GET /api/dashboard/email-analysis/{user_email}` - Get email analysis

**Dependencies**:
- Uses: `SendLog`, `ProfessorContact`, `EmailQueue` ORM models
- Returns: `DashboardStats` schema

#### `api/routes/email_templates.py`

**Endpoints**:
- `POST /api/email-templates/` - Create template
- `GET /api/email-templates/{user_email}` - List templates
- `GET /api/email-templates/{user_email}/{template_id}` - Get template
- `PUT /api/email-templates/{template_id}` - Update template
- `DELETE /api/email-templates/{template_id}` - Delete template

**Dependencies**:
- Uses: `EmailTemplate` ORM model
- Uses: `EmailTemplateCreate`, `EmailTemplateResponse`, `EmailTemplateUpdate` schemas

#### `api/routes/sending_rules.py`

**Endpoints**:
- `POST /api/sending-rules/` - Create/update rules
- `GET /api/sending-rules/{user_email}` - Get rules
- `PATCH /api/sending-rules/{user_email}` - Update rules

**Dependencies**:
- Uses: `SendingRules` ORM model
- Uses: `SendingRulesCreate`, `SendingRulesResponse`, `SendingRulesUpdate` schemas

#### `api/routes/email_queue.py`

**Endpoints**:
- `POST /api/email-queue/` - Add to queue
- `GET /api/email-queue/{user_email}` - Get queue items
- `PATCH /api/email-queue/{queue_id}/status` - Update status
- `GET /api/email-queue/logs/{user_email}` - Get send logs

**Dependencies**:
- Uses: `EmailQueue`, `SendLog` ORM models
- Uses: `EmailQueueCreate`, `EmailQueueResponse`, `SendLogResponse` schemas

## Data Flow Example

### Creating an Email Template

```
1. HTTP Request
   POST /api/email-templates/
   Body: {
     "user_email": "user@example.com",
     "template_body": "<html>...</html>",
     "template_type": 0,
     "subject": "Hello"
   }

2. FastAPI Router (email_templates.py)
   - Receives request
   - Validates with EmailTemplateCreate schema
   - Gets database session via Depends(get_db)

3. ORM Operation
   - Creates EmailTemplate instance
   - Adds to session: db.add(template)
   - Commits: db.commit()

4. Database
   - SQLAlchemy generates: INSERT INTO email_templates ...
   - PostgreSQL executes query

5. Response
   - ORM model converted to EmailTemplateResponse schema
   - Serialized to JSON
   - Returned to client
```

### Getting Dashboard Statistics

```
1. HTTP Request
   GET /api/dashboard/stats/user@example.com

2. FastAPI Router (dashboard.py)
   - Gets database session via Depends(get_db)

3. ORM Queries
   - db.query(SendLog).filter(...).count()
   - db.query(ProfessorContact).filter(...).count()
   - db.query(EmailQueue).filter(...).count()

4. Database
   - SQLAlchemy generates SQL queries
   - PostgreSQL executes queries

5. Response
   - Results aggregated into DashboardStats schema
   - Serialized to JSON
   - Returned to client
```

## Setup Instructions

### 1. Install Dependencies

**Python 3.12 Recommended** (Python 3.9+ supported)

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Key Dependencies**:
- `fastapi>=0.115.0` - Web framework (Python 3.12 compatible)
- `uvicorn[standard]>=0.32.0` - ASGI server
- `sqlalchemy>=2.0.36` - ORM (using DeclarativeBase for Python 3.12)
- `psycopg[binary]>=3.2.0` - PostgreSQL driver
- `pydantic>=2.9.0` - Schema validation
- `python-dotenv>=1.0.1` - Environment variables

### 2. Setup Database

**First Time Setup:**
The database `applyche_global` must be created before starting the API:

```bash
# Run the database setup script
python setup_database.py
```

This will:
- ✅ Create the `applyche_global` database
- ✅ Optionally initialize schema from SQL file
- ✅ Test the connection

**Configure Database Connection:**
The API automatically connects to PostgreSQL using settings from `model/server_info.env`.

**Quick Setup (Local PostgreSQL 18):**
```bash
# Use the helper script (recommended)
python switch_db_config.py local

# Or manually edit model/server_info.env
```

**Current Configuration:**
Ensure `model/server_info.env` contains:
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

**Switching to Remote Server:**
```bash
# Use helper script
python switch_db_config.py remote

# Then edit model/server_info.env with your server details:
# DB_USER=your_username
# DB_PASS=your_password
# DB_HOST=your_server_ip_or_domain
# DB_PORT=5432
# DB_NAME=applyche_global
```

**All database connections** (`api/database.py`, `model/connect_db.py`, `model/dashboard_model.py`) automatically read from `model/server_info.env`. No code changes needed when switching databases!

**Test Connection:**
```bash
python switch_db_config.py test
```

See `QUICK_DB_SWITCH_GUIDE.md` for detailed instructions.

### 3. Start the API Server

```bash
python start_api.py
```

Or using uvicorn directly:
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **API Root**: http://localhost:8000/

## API Endpoints

### Dashboard
- `GET /api/dashboard/stats/{user_email}` - Get dashboard statistics
- `GET /api/dashboard/email-analysis/{user_email}?email_type={type}` - Get email analysis

### Email Templates
- `POST /api/email-templates/` - Create email template
- `GET /api/email-templates/{user_email}` - Get all templates for user
- `GET /api/email-templates/{user_email}/{template_id}` - Get specific template
- `PUT /api/email-templates/{template_id}?user_email={email}` - Update template
- `DELETE /api/email-templates/{template_id}?user_email={email}` - Delete template

### Sending Rules
- `POST /api/sending-rules/` - Create/update sending rules
- `GET /api/sending-rules/{user_email}` - Get sending rules
- `PATCH /api/sending-rules/{user_email}` - Partially update rules

### Email Queue
- `POST /api/email-queue/` - Add email to queue
- `GET /api/email-queue/{user_email}` - Get queue items
- `PATCH /api/email-queue/{queue_id}/status` - Update queue status
- `GET /api/email-queue/logs/{user_email}` - Get send logs

## Integration with main_ui.py

### Using the API Client

The `api_client.py` module provides a Python client for interacting with the API:

```python
from api_client import ApplyCheAPIClient

# Initialize client
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

### Example Integration

See `example_integration.py` for complete examples of integrating the API client into `main_ui.py` components.

## Key Changes Made

### 1. Created FastAPI Application
- **Before**: Direct database connections in PyQt6 app
- **After**: RESTful API with FastAPI
- **Benefit**: Separation of concerns, API can be used by multiple clients

### 2. Converted to SQLAlchemy ORM
- **Before**: Raw SQL queries with psycopg
- **After**: SQLAlchemy ORM models
- **Benefit**: Type safety, relationship management, easier maintenance

### 3. Added Pydantic Schemas
- **Before**: No request/response validation
- **After**: Automatic validation with Pydantic
- **Benefit**: Type safety, automatic documentation, error handling

### 4. Structured API Routes
- **Before**: Database logic scattered in controllers
- **After**: Organized REST endpoints
- **Benefit**: Clear API structure, easy to extend

### 5. Database Session Management
- **Before**: Manual connection management
- **After**: Automatic session management via FastAPI dependencies
- **Benefit**: Proper connection pooling, automatic cleanup

## Database Models Overview

The ORM includes 25+ models covering:

### Core Models
- `User` - User accounts
- `UserEducationInformation` - Education details
- `University`, `Department` - University data
- `Professor`, `ProfessorResearchInterest` - Professor profiles

### Email System
- `EmailTemplate`, `TemplateFile` - Email templates
- `SendingRules` - Sending configuration
- `EmailQueue` - Email queue
- `SendLog` - Send history

### Contact & Positions
- `ProfessorContact` - Contact tracking
- `OpenPosition` - Open positions
- `SavedPosition` - User bookmarks

### Reviews & Social
- `ProfessorReview` - Reviews
- `Comment`, `ReviewVote`, `CommentVote` - Comments and votes

### Subscriptions
- `Subscription`, `SubscriptionHistory` - Premium subscriptions

### Utilities
- `ChatLog`, `APIToken`, `Metric` - Various utilities
- `ProfessorList`, `EmailProperty`, `File` - File management

## Relationships

Models are connected via SQLAlchemy relationships:

- **User** has many: EmailTemplates, SendingRules, EmailQueue items, SendLogs, etc.
- **EmailTemplate** belongs to: User, has many: TemplateFiles, EmailQueue items, SendLogs
- **SendingRules** belongs to: User (one-to-one)
- **EmailQueue** belongs to: User, EmailTemplate
- **SendLog** belongs to: User, EmailTemplate

## Error Handling

All routes include proper error handling:
- HTTP exceptions for client errors (400, 404)
- Database rollback on errors
- Detailed error messages

## Testing

### Health Check
```bash
curl http://localhost:8000/health
```

### Test Endpoint
```bash
curl http://localhost:8000/api/dashboard/stats/user@example.com
```

## Documentation Files

- **README.md** (this file) - Main project documentation
- **DEPENDENCY_GRAPH.md** - Detailed dependency graph
- **dependency_graph.mmd** - Mermaid diagram source
- **README_ORM.md** - ORM-specific documentation
- **MIGRATION_TO_ORM.md** - Migration guide
- **DATABASE_CONFIGURATION.md** - Database setup and configuration guide
- **QUICK_DB_SWITCH_GUIDE.md** - Quick guide to switch between local/remote databases
- **API_CONNECTION_HANDLING.md** - API connection error handling
- **PERFORMANCE_OPTIMIZATIONS.md** - Performance improvements

## Future Enhancements

1. **Service Layer**: Add business logic layer between routers and models
2. **Authentication**: Add JWT token authentication
3. **Alembic Migrations**: Set up database migrations
4. **Caching**: Add Redis caching for frequently accessed data
5. **Background Tasks**: Add Celery for async email sending
6. **API Versioning**: Add versioning support
7. **Rate Limiting**: Add rate limiting middleware
8. **Logging**: Add structured logging

## Troubleshooting

### Database Connection Issues

**Database Does Not Exist:**
```
Error: database "applyche_global" does not exist
```
**Solution:** Run `python setup_database.py` to create the database.

**Other Connection Issues:**
- Check `model/server_info.env` credentials
- Ensure PostgreSQL 18 is running on port 5434 (or your configured port)
- Verify database exists: `applyche_global`
- Test connection: `python switch_db_config.py test`
- For remote servers, ensure:
  - Firewall allows connections on the configured port
  - PostgreSQL `pg_hba.conf` allows connections from your IP
  - Server is listening on the correct interface (not just localhost)

### Import Errors
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python path includes project root

### Port Already in Use
- Change port in `start_api.py` or use different port with uvicorn

## Support

For issues or questions:
1. Check API documentation at `/docs`
2. Review `DEPENDENCY_GRAPH.md` for architecture details
3. See `example_integration.py` for usage examples

## Python 3.12 Compatibility

This codebase has been updated for Python 3.12 compatibility:

- ✅ Updated SQLAlchemy to use `DeclarativeBase` (replaces deprecated `declarative_base()`)
- ✅ Removed deprecated `future=True` parameter from SQLAlchemy engine
- ✅ Updated all dependencies to Python 3.12 compatible versions
- ✅ Cleaned repository of Python 3.9 cache files
- ✅ Added `.gitignore` to prevent cache file commits

See `PYTHON_3.12_MIGRATION.md` for detailed migration information.

## Repository Cleanup

The repository has been cleaned:
- ✅ Removed all `__pycache__` directories
- ✅ Removed all `.pyc` files
- ✅ Added `.gitignore` to prevent future cache commits

To clean the repository manually:
```bash
python clean_repo.py
```

## License

[Add your license information here]

