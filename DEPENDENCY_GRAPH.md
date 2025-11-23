# ApplyChe API - Complete Dependency Graph

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Application                      │
│                         (api/main.py)                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ includes
                             ▼
        ┌────────────────────────────────────────┐
        │          API Routers Layer             │
        │        (api/routes/*.py)               │
        └────────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Dashboard   │    │ Email        │    │ Sending      │
│  Router      │    │ Templates    │    │ Rules        │
│              │    │ Router       │    │ Router       │
└──────────────┘    └──────────────┘    └──────────────┘
        │                    │                    │
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Email Queue │    │  Schemas     │    │  Database    │
│  Router      │    │ (Pydantic)   │    │  Session     │
└──────────────┘    └──────────────┘    └──────────────┘
        │                    │                    │
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  ORM Models     │
                    │ (SQLAlchemy)    │
                    └─────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  PostgreSQL     │
                    │   Database      │
                    └─────────────────┘
```

## Detailed Dependency Graph

### 1. Router Layer → Schema Layer

#### Dashboard Router (`api/routes/dashboard.py`)
```
dashboard.router
    ├── GET /api/dashboard/stats/{user_email}
    │   └── Uses: DashboardStats (response)
    │
    └── GET /api/dashboard/email-analysis/{user_email}
        └── Returns: Dict (email_type, count)
```

#### Email Templates Router (`api/routes/email_templates.py`)
```
email_templates.router
    ├── POST /api/email-templates/
    │   ├── Uses: EmailTemplateCreate (request)
    │   └── Returns: EmailTemplateResponse (response)
    │
    ├── GET /api/email-templates/{user_email}
    │   └── Returns: List[EmailTemplateResponse]
    │
    ├── GET /api/email-templates/{user_email}/{template_id}
    │   └── Returns: EmailTemplateResponse
    │
    ├── PUT /api/email-templates/{template_id}
    │   ├── Uses: EmailTemplateUpdate (request)
    │   └── Returns: EmailTemplateResponse
    │
    └── DELETE /api/email-templates/{template_id}
        └── Returns: MessageResponse
```

#### Sending Rules Router (`api/routes/sending_rules.py`)
```
sending_rules.router
    ├── POST /api/sending-rules/
    │   ├── Uses: SendingRulesCreate (request)
    │   └── Returns: SendingRulesResponse (response)
    │
    ├── GET /api/sending-rules/{user_email}
    │   └── Returns: SendingRulesResponse
    │
    └── PATCH /api/sending-rules/{user_email}
        ├── Uses: SendingRulesUpdate (request)
        └── Returns: SendingRulesResponse
```

#### Email Queue Router (`api/routes/email_queue.py`)
```
email_queue.router
    ├── POST /api/email-queue/
    │   ├── Uses: EmailQueueCreate (request)
    │   └── Returns: EmailQueueResponse (response)
    │
    ├── GET /api/email-queue/{user_email}
    │   └── Returns: List[EmailQueueResponse]
    │
    ├── PATCH /api/email-queue/{queue_id}/status
    │   └── Returns: MessageResponse
    │
    └── GET /api/email-queue/logs/{user_email}
        └── Returns: List[SendLogResponse]
```

### 2. Router Layer → ORM Model Layer

#### Dashboard Router → Models
```
dashboard.router
    ├── get_dashboard_stats()
    │   ├── Uses: SendLog (ORM)
    │   ├── Uses: ProfessorContact (ORM)
    │   └── Uses: EmailQueue (ORM)
    │
    └── get_email_analysis()
        └── Uses: SendLog (ORM)
```

#### Email Templates Router → Models
```
email_templates.router
    ├── create_email_template()
    │   └── Uses: EmailTemplate (ORM)
    │
    ├── get_email_templates()
    │   └── Uses: EmailTemplate (ORM)
    │
    ├── get_email_template()
    │   └── Uses: EmailTemplate (ORM)
    │
    ├── update_email_template()
    │   └── Uses: EmailTemplate (ORM)
    │
    └── delete_email_template()
        └── Uses: EmailTemplate (ORM)
```

#### Sending Rules Router → Models
```
sending_rules.router
    ├── create_sending_rules()
    │   └── Uses: SendingRules (ORM)
    │
    ├── get_sending_rules()
    │   └── Uses: SendingRules (ORM)
    │
    └── update_sending_rules()
        └── Uses: SendingRules (ORM)
```

#### Email Queue Router → Models
```
email_queue.router
    ├── create_email_queue_item()
    │   └── Uses: EmailQueue (ORM)
    │
    ├── get_email_queue()
    │   └── Uses: EmailQueue (ORM)
    │
    ├── update_queue_status()
    │   └── Uses: EmailQueue (ORM)
    │
    └── get_send_logs()
        └── Uses: SendLog (ORM)
```

### 3. Schema Layer Details

#### Request Schemas (Pydantic)
```
api/models.py
    ├── EmailTemplateCreate
    │   ├── user_email: EmailStr
    │   ├── template_body: str
    │   ├── template_type: int
    │   └── subject: Optional[str]
    │
    ├── EmailTemplateUpdate
    │   ├── template_body: Optional[str]
    │   ├── template_type: Optional[int]
    │   └── subject: Optional[str]
    │
    ├── SendingRulesCreate
    │   ├── user_email: EmailStr
    │   ├── main_mail_number: int
    │   ├── reminder_one: int
    │   ├── reminder_two: int
    │   ├── reminder_three: int
    │   ├── local_professor_time: bool
    │   ├── max_email_per_university: int
    │   ├── send_working_day_only: bool
    │   ├── period_between_reminders: int
    │   ├── delay_sending_mail: int
    │   └── start_time_send: Optional[str]
    │
    ├── SendingRulesUpdate
    │   └── (all fields Optional)
    │
    ├── EmailQueueCreate
    │   ├── user_email: EmailStr
    │   ├── to_email: EmailStr
    │   ├── subject: Optional[str]
    │   ├── body: str
    │   ├── template_id: Optional[int]
    │   └── scheduled_at: datetime
    │
    ├── UserCreate
    │   ├── email: EmailStr
    │   ├── password_hash: str
    │   └── display_name: Optional[str]
    │
    └── MessageResponse
        ├── message: str
        └── success: bool
```

#### Response Schemas (Pydantic)
```
api/models.py
    ├── DashboardStats
    │   ├── email_you_send: int
    │   ├── first_reminder_send: int
    │   ├── second_reminder_send: int
    │   ├── third_reminder_send: int
    │   ├── number_of_email_professor_answered: int
    │   └── emails_remaining: int
    │
    ├── EmailTemplateResponse
    │   ├── id: int
    │   ├── user_email: str
    │   ├── template_body: str
    │   ├── template_type: int
    │   ├── subject: Optional[str]
    │   └── created_at: datetime
    │
    ├── SendingRulesResponse
    │   ├── id: int
    │   ├── user_email: str
    │   ├── main_mail_number: int
    │   ├── reminder_one: int
    │   ├── reminder_two: int
    │   ├── reminder_three: int
    │   ├── local_professor_time: bool
    │   ├── max_email_per_university: int
    │   ├── send_working_day_only: bool
    │   ├── period_between_reminders: int
    │   ├── delay_sending_mail: int
    │   ├── start_time_send: Optional[str]
    │   └── created_at: datetime
    │
    ├── EmailQueueResponse
    │   ├── id: int
    │   ├── user_email: str
    │   ├── to_email: str
    │   ├── subject: Optional[str]
    │   ├── body: str
    │   ├── template_id: Optional[int]
    │   ├── scheduled_at: datetime
    │   ├── status: int
    │   ├── retry_count: int
    │   └── created_at: datetime
    │
    ├── SendLogResponse
    │   ├── id: int
    │   ├── user_email: str
    │   ├── sent_to: str
    │   ├── sent_time: datetime
    │   ├── subject: Optional[str]
    │   ├── send_type: int
    │   └── delivery_status: int
    │
    ├── UserResponse
    │   ├── email: str
    │   ├── created_at: datetime
    │   ├── last_login: Optional[datetime]
    │   ├── is_active: bool
    │   ├── display_name: Optional[str]
    │   └── profile_image: Optional[str]
    │
    └── ProfessorResponse
        ├── email: str
        ├── name: str
        ├── major: Optional[str]
        ├── university_id: Optional[int]
        ├── department_id: Optional[int]
        ├── professor_img: Optional[str]
        └── meta_data: Optional[Dict[str, Any]]
```

### 4. ORM Model Layer Details

#### Core Models (`api/db_models.py`)
```
Base (declarative_base)
    │
    ├── User
    │   ├── email (PK, CITEXT)
    │   ├── password_hash
    │   ├── created_at
    │   └── Relationships:
    │       ├── → EmailTemplate
    │       ├── → SendingRules
    │       ├── → EmailQueue
    │       ├── → SendLog
    │       ├── → ProfessorContact
    │       └── → (many more...)
    │
    ├── EmailTemplate
    │   ├── id (PK)
    │   ├── user_email (FK → User)
    │   ├── template_body
    │   ├── template_type
    │   ├── subject
    │   └── Relationships:
    │       ├── ← User
    │       ├── → TemplateFile
    │       ├── → EmailQueue
    │       └── → SendLog
    │
    ├── SendingRules
    │   ├── id (PK)
    │   ├── user_email (FK → User, unique)
    │   ├── main_mail_number
    │   ├── reminder_one
    │   ├── reminder_two
    │   ├── reminder_three
    │   ├── local_professor_time
    │   ├── max_email_per_university
    │   ├── send_working_day_only
    │   ├── period_between_reminders
    │   ├── delay_sending_mail
    │   ├── start_time_send
    │   └── Relationships:
    │       └── ← User
    │
    ├── EmailQueue
    │   ├── id (PK, BigInteger)
    │   ├── user_email (FK → User)
    │   ├── to_email
    │   ├── subject
    │   ├── body
    │   ├── template_id (FK → EmailTemplate)
    │   ├── scheduled_at
    │   ├── status
    │   ├── retry_count
    │   └── Relationships:
    │       ├── ← User
    │       └── ← EmailTemplate
    │
    ├── SendLog
    │   ├── id (PK, BigInteger)
    │   ├── user_email (FK → User)
    │   ├── sent_to
    │   ├── sent_time
    │   ├── subject
    │   ├── body
    │   ├── template_id (FK → EmailTemplate)
    │   ├── send_type
    │   ├── delivery_status
    │   └── Relationships:
    │       ├── ← User
    │       └── ← EmailTemplate
    │
    ├── ProfessorContact
    │   ├── id (PK)
    │   ├── user_email (FK → User)
    │   ├── professor_email (FK → Professor)
    │   ├── position_id (FK → OpenPosition)
    │   ├── contact_status
    │   └── Relationships:
    │       ├── ← User
    │       ├── ← Professor
    │       └── ← OpenPosition
    │
    └── (25+ more models...)
```

### 5. Database Layer

```
api/database.py
    ├── engine (SQLAlchemy Engine)
    │   └── Connection: PostgreSQL
    │
    ├── SessionLocal (Session Factory)
    │   └── Creates: SQLAlchemy Session
    │
    ├── get_db() (Dependency Function)
    │   └── Used by: All routers via Depends()
    │
    └── get_db_session() (Context Manager)
        └── For: Manual session management
```

## Complete Dependency Flow

### Example: Creating Email Template

```
1. HTTP Request
   POST /api/email-templates/
   Body: EmailTemplateCreate (JSON)

2. FastAPI Router
   api/routes/email_templates.py
   └── create_email_template()
       ├── Receives: EmailTemplateCreate (Pydantic)
       └── Depends: get_db() → Session

3. ORM Operation
   db.add(EmailTemplate(...))
   db.commit()

4. Database
   INSERT INTO email_templates (...)

5. Response
   EmailTemplateResponse (Pydantic)
   └── Converted to JSON
```

### Example: Getting Dashboard Stats

```
1. HTTP Request
   GET /api/dashboard/stats/{user_email}

2. FastAPI Router
   api/routes/dashboard.py
   └── get_dashboard_stats()
       ├── Depends: get_db() → Session
       └── Queries:
           ├── db.query(SendLog).filter(...)
           ├── db.query(ProfessorContact).filter(...)
           └── db.query(EmailQueue).filter(...)

3. ORM Queries
   └── SQLAlchemy generates SQL

4. Database
   └── Executes SQL queries

5. Response
   DashboardStats (Pydantic)
   └── Converted to JSON
```

## Dependency Matrix

| Router | Endpoint | Request Schema | Response Schema | ORM Model | Database Table |
|--------|----------|----------------|-----------------|-----------|----------------|
| dashboard | GET /stats/{email} | - | DashboardStats | SendLog, ProfessorContact, EmailQueue | send_log, professor_contact, email_queue |
| dashboard | GET /email-analysis/{email} | - | Dict | SendLog | send_log |
| email_templates | POST / | EmailTemplateCreate | EmailTemplateResponse | EmailTemplate | email_templates |
| email_templates | GET /{email} | - | List[EmailTemplateResponse] | EmailTemplate | email_templates |
| email_templates | GET /{email}/{id} | - | EmailTemplateResponse | EmailTemplate | email_templates |
| email_templates | PUT /{id} | EmailTemplateUpdate | EmailTemplateResponse | EmailTemplate | email_templates |
| email_templates | DELETE /{id} | - | MessageResponse | EmailTemplate | email_templates |
| sending_rules | POST / | SendingRulesCreate | SendingRulesResponse | SendingRules | sending_rules |
| sending_rules | GET /{email} | - | SendingRulesResponse | SendingRules | sending_rules |
| sending_rules | PATCH /{email} | SendingRulesUpdate | SendingRulesResponse | SendingRules | sending_rules |
| email_queue | POST / | EmailQueueCreate | EmailQueueResponse | EmailQueue | email_queue |
| email_queue | GET /{email} | - | List[EmailQueueResponse] | EmailQueue | email_queue |
| email_queue | PATCH /{id}/status | - | MessageResponse | EmailQueue | email_queue |
| email_queue | GET /logs/{email} | - | List[SendLogResponse] | SendLog | send_log |

## Service Layer (Future)

Currently, business logic is directly in routers. A service layer could be added:

```
Routers → Services → ORM Models → Database
```

Example structure:
```
api/services/
    ├── email_template_service.py
    ├── sending_rules_service.py
    ├── dashboard_service.py
    └── email_queue_service.py
```

## Key Dependencies

### External Dependencies
- `fastapi` - Web framework
- `sqlalchemy` - ORM
- `pydantic` - Schema validation
- `psycopg` - PostgreSQL driver
- `uvicorn` - ASGI server

### Internal Dependencies
- `api.database` - Database connection (used by all routers)
- `api.models` - Pydantic schemas (used by all routers)
- `api.db_models` - ORM models (used by all routers)

## Notes

1. **No Service Layer**: Currently, routers directly interact with ORM models. Consider adding a service layer for complex business logic.

2. **Direct ORM Access**: Routers use SQLAlchemy ORM directly. This is fine for simple CRUD, but complex operations should be in services.

3. **Schema Validation**: All requests/responses are validated by Pydantic schemas automatically.

4. **Database Sessions**: All routes use `Depends(get_db)` for automatic session management.

5. **Error Handling**: HTTP exceptions are raised in routers, could be centralized in a service layer.

