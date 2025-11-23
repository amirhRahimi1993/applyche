# ApplyChe UML Documentation

This document provides comprehensive UML diagrams for the ApplyChe project, including database schema, API architecture, class structures, and workflow sequences.

## Table of Contents

1. [Database ER Diagram](#database-er-diagram)
2. [API Architecture Diagram](#api-architecture-diagram)
3. [Class Diagrams](#class-diagrams)
4. [Sequence Diagrams](#sequence-diagrams)
5. [Component Diagram](#component-diagram)

---

## Database ER Diagram

### Entity Relationship Diagram (Mermaid)

```mermaid
erDiagram
    USERS ||--o{ USER_EDUCATION_INFORMATION : has
    USERS ||--o{ SUBSCRIPTIONS : has
    USERS ||--o{ SUBSCRIPTION_HISTORY : has
    USERS ||--o{ EMAIL_TEMPLATES : creates
    USERS ||--o{ SENDING_RULES : configures
    USERS ||--o{ EMAIL_QUEUE : queues
    USERS ||--o{ SEND_LOG : logs
    USERS ||--o{ PROFESSOR_CONTACT : tracks
    USERS ||--o{ SAVED_POSITIONS : saves
    USERS ||--o{ PROFESSOR_REVIEW : writes
    USERS ||--o{ COMMENT : writes
    USERS ||--o{ CHAT_LOG : generates
    USERS ||--o{ API_TOKEN : uses
    USERS ||--o{ METRIC : tracks
    USERS ||--o{ PROFESSOR_LIST : uploads
    USERS ||--o{ EMAIL_PROPERTY : configures
    USERS ||--o{ FILE : owns

    UNIVERSITIES ||--o{ DEPARTMENTS : contains
    UNIVERSITIES ||--o{ USER_EDUCATION_INFORMATION : referenced_by
    UNIVERSITIES ||--o{ PROFESSORS : hosts
    UNIVERSITIES ||--o{ OPEN_POSITIONS : offers

    DEPARTMENTS ||--o{ PROFESSORS : contains
    DEPARTMENTS ||--o{ OPEN_POSITIONS : offers

    PROFESSORS ||--o{ PROFESSOR_RESEARCH_INTERESTS : has
    PROFESSORS ||--o{ OPEN_POSITIONS : supervises
    PROFESSORS ||--o{ PROFESSOR_CONTACT : contacted_by
    PROFESSORS ||--o{ PROFESSOR_REVIEW : reviewed

    EMAIL_TEMPLATES ||--o{ TEMPLATE_FILES : contains
    EMAIL_TEMPLATES ||--o{ EMAIL_QUEUE : used_in

    OPEN_POSITIONS ||--o{ PROFESSOR_CONTACT : referenced_in
    OPEN_POSITIONS ||--o{ SAVED_POSITIONS : saved_in

    PROFESSOR_REVIEW ||--o{ COMMENT : has
    PROFESSOR_REVIEW ||--o{ REVIEW_VOTE : receives
    COMMENT ||--o{ COMMENT_VOTE : receives

    USERS {
        CITEXT email PK
        TEXT password_hash
        TEXT password_salt
        TIMESTAMP created_at
        TIMESTAMP last_login
        SMALLINT failed_login_attempts
        BOOLEAN is_active
        TEXT display_name
        TEXT profile_image
        TEXT personal_website
        CITEXT backup_email
    }

    USER_EDUCATION_INFORMATION {
        INT id PK
        CITEXT user_email FK
        TEXT major
        INT university_id FK
        TEXT university_department
        STRING education_level
        NUMERIC grade
        NUMERIC ielts
        NUMERIC gre
        TEXT google_scholar_link
        TEXT CV_path
        TEXT SOP_path
        TIMESTAMP created_at
    }

    UNIVERSITIES {
        INT id PK
        TEXT name
        CHAR country
        TEXT website
    }

    DEPARTMENTS {
        INT id PK
        INT university_id FK
        TEXT university_deparment_name
    }

    PROFESSORS {
        CITEXT email PK
        TEXT name
        TEXT major
        INT university_id FK
        INT department_id FK
        TEXT professor_img
        JSONB meta_data
    }

    PROFESSOR_RESEARCH_INTERESTS {
        INT id PK
        CITEXT professor_email FK
        TEXT interest
    }

    OPEN_POSITIONS {
        BIGINT id PK
        INT university_id FK
        INT department_id FK
        TEXT position_title
        TEXT fund
        NUMERIC min_ielts
        NUMERIC min_gre
        CITEXT contact_email
        JSONB requirements
        CITEXT supervisor_email FK
        DATE deadline
        TEXT description
        TEXT more_info_link
        SMALLINT graduate_level
        JSONB meta_data
        TEXT country
    }

    PROFESSOR_CONTACT {
        INT id PK
        CITEXT user_email FK
        CITEXT professor_email FK
        BIGINT position_id FK
        TIMESTAMP last_contact_time
        TIMESTAMP next_contact_time
        SMALLINT contact_status
        BOOLEAN is_active
        SMALLINT attempts
    }

    SAVED_POSITIONS {
        INT id PK
        CITEXT user_email FK
        BIGINT position_id FK
        SMALLINT status
        TEXT notes
        TIMESTAMP created_at
    }

    EMAIL_TEMPLATES {
        INT id PK
        CITEXT user_email FK
        TEXT template_body
        SMALLINT template_type
        TEXT subject
        TIMESTAMP created_at
    }

    TEMPLATE_FILES {
        INT id PK
        INT email_template_id FK
        TEXT file_path
    }

    SENDING_RULES {
        INT id PK
        CITEXT user_email FK
        SMALLINT main_mail_number
        SMALLINT reminder_one
        SMALLINT reminder_two
        SMALLINT reminder_three
        BOOLEAN local_professor_time
        SMALLINT max_email_per_university
        BOOLEAN send_working_day_only
        SMALLINT period_between_reminders
        SMALLINT delay_sending_mail
        TIME start_time_send
        TIMESTAMP created_at
    }

    EMAIL_QUEUE {
        INT id PK
        CITEXT user_email FK
        CITEXT to_email
        TEXT subject
        TEXT body
        INT template_id FK
        TIMESTAMP scheduled_at
        SMALLINT status
        SMALLINT retry_count
        TIMESTAMP created_at
    }

    SEND_LOG {
        INT id PK
        CITEXT user_email FK
        CITEXT sent_to
        TIMESTAMP sent_time
        TEXT subject
        SMALLINT send_type
        SMALLINT delivery_status
    }

    SUBSCRIPTIONS {
        INT id PK
        CITEXT user_email FK
        VARCHAR plan_name
        TIMESTAMP started_at
        TIMESTAMP expires_at
        SMALLINT status
    }

    SUBSCRIPTION_HISTORY {
        INT id PK
        CITEXT user_email FK
        VARCHAR plan_name
        TIMESTAMP started_at
        TIMESTAMP ended_at
        TEXT payment_reference
        SMALLINT status
        TIMESTAMP created_at
    }

    PROFESSOR_REVIEW {
        INT id PK
        CITEXT user_email FK
        CITEXT professor_email FK
        TEXT review_text
        NUMERIC rating
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    COMMENT {
        INT id PK
        INT review_id FK
        CITEXT commenter_email FK
        TEXT comment_text
        TIMESTAMP created_at
    }

    REVIEW_VOTE {
        INT id PK
        INT review_id FK
        CITEXT voter_email FK
        SMALLINT vote_type
        TIMESTAMP created_at
    }

    COMMENT_VOTE {
        INT id PK
        INT comment_id FK
        CITEXT voter_email FK
        SMALLINT vote_type
        TIMESTAMP created_at
    }

    CHAT_LOG {
        INT id PK
        CITEXT user_email FK
        TEXT user_message
        TEXT bot_response
        TIMESTAMP created_at
    }

    API_TOKEN {
        INT id PK
        CITEXT user_email FK
        TEXT token_hash
        TIMESTAMP expires_at
        TIMESTAMP created_at
    }

    METRIC {
        INT id PK
        CITEXT user_email FK
        TEXT metric_name
        NUMERIC metric_value
        TIMESTAMP recorded_at
    }

    PROFESSOR_LIST {
        INT id PK
        CITEXT user_email FK
        TEXT file_path
        TIMESTAMP uploaded_at
    }

    EMAIL_PROPERTY {
        INT id PK
        CITEXT user_email FK
        TEXT property_key
        TEXT property_value
        TIMESTAMP updated_at
    }

    FILE {
        INT id PK
        CITEXT owner_email FK
        TEXT file_path
        TEXT file_type
        BIGINT file_size
        TIMESTAMP uploaded_at
    }
```

---

## API Architecture Diagram

### FastAPI Application Structure (Mermaid)

```mermaid
graph TB
    subgraph "Client Layer"
        UI[PyQt6 Desktop App<br/>main_ui.py]
        WEB[Web Client<br/>Optional]
    end

    subgraph "API Layer - FastAPI"
        MAIN[main.py<br/>FastAPI App]
        CORS[CORS Middleware]
        
        subgraph "Routers"
            DASH[dashboard.py<br/>Dashboard Stats]
            TEMP[email_templates.py<br/>Template CRUD]
            RULES[sending_rules.py<br/>Sending Config]
            QUEUE[email_queue.py<br/>Queue Management]
        end
        
        subgraph "Schemas"
            MODELS[models.py<br/>Pydantic Schemas]
        end
    end

    subgraph "Database Layer"
        DB[database.py<br/>Session Management]
        ORM[db_models.py<br/>SQLAlchemy ORM]
        PG[(PostgreSQL<br/>Database)]
    end

    UI -->|HTTP Requests| MAIN
    WEB -->|HTTP Requests| MAIN
    MAIN --> CORS
    MAIN --> DASH
    MAIN --> TEMP
    MAIN --> RULES
    MAIN --> QUEUE
    
    DASH --> MODELS
    TEMP --> MODELS
    RULES --> MODELS
    QUEUE --> MODELS
    
    DASH --> DB
    TEMP --> DB
    RULES --> DB
    QUEUE --> DB
    
    DB --> ORM
    ORM --> PG
```

### API Component Diagram (PlantUML)

```plantuml
@startuml API Architecture
package "FastAPI Application" {
    [main.py] as Main
    [CORS Middleware] as CORS
}

package "API Routes" {
    [dashboard.py] as Dashboard
    [email_templates.py] as Templates
    [sending_rules.py] as Rules
    [email_queue.py] as Queue
}

package "Schemas" {
    [models.py] as Schemas
}

package "Database" {
    [database.py] as DB
    [db_models.py] as ORM
    database PostgreSQL
}

Main --> CORS
Main --> Dashboard
Main --> Templates
Main --> Rules
Main --> Queue

Dashboard --> Schemas
Templates --> Schemas
Rules --> Schemas
Queue --> Schemas

Dashboard --> DB
Templates --> DB
Rules --> DB
Queue --> DB

DB --> ORM
ORM --> PostgreSQL
@enduml
```

---

## Class Diagrams

### Existing Code Structure (Mermaid)

```mermaid
classDiagram
    class MyWindow {
        -widget_content
        -stacked_content
        -email_Temp
        -professorList
        -email_prep
        -statics
        -dashboard
        +__init__()
        +hamburger_toggle()
        +__btn_page_home_arise()
        +__btn_page_email_template()
        +btn_page_prepare_send_email()
        +_setup_resizable_layout()
        +_configure_widget_resize()
        +_finalize_resize_configuration()
    }

    class Dashboard {
        -widget
        -model
        +__init__(widget)
        +report()
        +chart_email_answered_by_professor()
        +chart_email_send_remain()
        +chart_emaill_send_by_reminder()
    }

    class EmailEditor {
        -widget
        -stacked_widget
        -middle_info_pass
        -uploaded_files
        -saved_templates
        -text_edits
        +__init__(widget, middle_info_pass)
        +save_template_data(template_key)
        +toggle_bold(editor, button)
        +toggle_italic(editor, button)
        +insert_link(editor)
        +insert_file_attachment(editor)
    }

    class Prepare_send_mail {
        -widget
        -middle_info_pass
        -bus
        -coordinator
        +__init__(widget, middle_info_pass)
        +prepare_email()
        +start_sending()
        +stop_sending()
    }

    class Professor_lists {
        -widget
        -middle_info_pass
        -controller
        -tbl_professors_list
        +__init__(widget, middle_info_pass)
        +load_professors()
        +display_professors()
    }

    class Statics {
        -widget
        -chart_widget
        -chart_layout
        +__init__(widget)
        +generate_charts()
    }

    class DashboardController {
        -secret_key
        +__init__()
        +fetch_data_from_model()
        +give_data_to_view()
        +give_data_to_model()
        +fetch_data_from_view()
    }

    class ProfessorsController {
        -path
        -header
        -nan_columns
        -df
        +__init__(path)
        +send_professor_info()
    }

    class SendMailController {
        -bus
        -_sending
        -_thread
        -info
        -is_premium
        -EMAIL_PROVIDERS
        +__init__(bus)
        +start_sending(info)
        +stop_sending()
        -_send_loop()
    }

    class EmailTemplateModel {
        -connection
        -cursor
        +__init__()
        +upload_text(text)
        +fetch_text()
    }

    class Dashboard_model {
        -db_name
        -username
        -password
        -host
        -column_storage
        -conn
        +__init__()
        -__connect()
        +analysis_email(key)
        +return_not_send_mail()
    }

    class connect_to_db {
        -db_name
        -username
        -password
        -host
        -column_storage
        -conn
        +__init__()
        +return_username_password()
        +connect()
    }

    class EventBus {
        -_subscribers
        +__init__()
        +subscribe(event_name, callback)
        +publish(event_name, data)
    }

    class Coordinator {
        -bus
        -view
        -controller
        +__init__(bus)
        +set_view(view)
        +start_sending(info)
        +stop_sending()
        -_on_log_received(message)
    }

    class middle_info_pass {
        -store_data_variable
        +__init__()
        +store_data(key, value)
        +get_data(key)
    }

    class CheckPremium {
        +__init__(email, password)
        +check_premium()
    }

    MyWindow --> Dashboard
    MyWindow --> EmailEditor
    MyWindow --> Prepare_send_mail
    MyWindow --> Professor_lists
    MyWindow --> Statics

    Dashboard --> Dashboard_model
    Dashboard_model --> connect_to_db

    EmailEditor --> middle_info_pass
    Prepare_send_mail --> middle_info_pass
    Prepare_send_mail --> Coordinator
    Prepare_send_mail --> EventBus

    Professor_lists --> ProfessorsController

    Coordinator --> SendMailController
    Coordinator --> EventBus
    SendMailController --> EventBus
    SendMailController --> CheckPremium

    EmailTemplateModel --> connect_to_db
```

### API Class Diagram (Mermaid)

```mermaid
classDiagram
    class FastAPI {
        +app
        +include_router()
    }

    class APIRouter {
        +router
        +prefix
        +tags
    }

    class DashboardRouter {
        +get_dashboard_stats()
        +get_email_analysis()
    }

    class EmailTemplatesRouter {
        +create_email_template()
        +get_email_templates()
        +get_email_template()
        +update_email_template()
        +delete_email_template()
    }

    class SendingRulesRouter {
        +create_sending_rules()
        +get_sending_rules()
        +update_sending_rules()
    }

    class EmailQueueRouter {
        +create_email_queue()
        +get_email_queue()
        +get_send_logs()
    }

    class BaseModel {
        <<Pydantic>>
    }

    class DashboardStats {
        +email_you_send
        +first_reminder_send
        +second_reminder_send
        +third_reminder_send
        +number_of_email_professor_answered
        +emails_remaining
    }

    class EmailTemplateCreate {
        +user_email
        +template_body
        +template_type
        +subject
    }

    class EmailTemplateResponse {
        +id
        +user_email
        +template_body
        +template_type
        +subject
        +created_at
    }

    class SendingRulesCreate {
        +user_email
        +main_mail_number
        +reminder_one
        +reminder_two
        +reminder_three
        +local_professor_time
        +max_email_per_university
        +send_working_day_only
        +period_between_reminders
        +delay_sending_mail
        +start_time_send
    }

    class EmailQueueCreate {
        +user_email
        +to_email
        +subject
        +body
        +template_id
        +scheduled_at
    }

    class Session {
        <<SQLAlchemy>>
        +query()
        +add()
        +commit()
        +delete()
    }

    class Base {
        <<SQLAlchemy>>
    }

    class User {
        +email
        +password_hash
        +created_at
        +is_active
    }

    class EmailTemplate {
        +id
        +user_email
        +template_body
        +template_type
        +subject
        +created_at
    }

    class SendingRules {
        +id
        +user_email
        +main_mail_number
        +reminder_one
        +reminder_two
        +reminder_three
        +local_professor_time
        +max_email_per_university
        +send_working_day_only
        +period_between_reminders
        +delay_sending_mail
        +start_time_send
    }

    class EmailQueue {
        +id
        +user_email
        +to_email
        +subject
        +body
        +template_id
        +scheduled_at
        +status
        +retry_count
    }

    class SendLog {
        +id
        +user_email
        +sent_to
        +sent_time
        +subject
        +send_type
        +delivery_status
    }

    FastAPI --> APIRouter
    APIRouter <|-- DashboardRouter
    APIRouter <|-- EmailTemplatesRouter
    APIRouter <|-- SendingRulesRouter
    APIRouter <|-- EmailQueueRouter

    DashboardRouter --> DashboardStats
    EmailTemplatesRouter --> EmailTemplateCreate
    EmailTemplatesRouter --> EmailTemplateResponse
    SendingRulesRouter --> SendingRulesCreate
    EmailQueueRouter --> EmailQueueCreate

    DashboardStats --|> BaseModel
    EmailTemplateCreate --|> BaseModel
    EmailTemplateResponse --|> BaseModel
    SendingRulesCreate --|> BaseModel
    EmailQueueCreate --|> BaseModel

    DashboardRouter --> Session
    EmailTemplatesRouter --> Session
    SendingRulesRouter --> Session
    EmailQueueRouter --> Session

    Session --> User
    Session --> EmailTemplate
    Session --> SendingRules
    Session --> EmailQueue
    Session --> SendLog

    User --|> Base
    EmailTemplate --|> Base
    SendingRules --|> Base
    EmailQueue --|> Base
    SendLog --|> Base
```

---

## Sequence Diagrams

### Email Sending Workflow (Mermaid)

```mermaid
sequenceDiagram
    participant UI as PyQt6 UI
    participant Prep as Prepare_send_mail
    participant Coord as Coordinator
    participant Bus as EventBus
    participant Ctrl as SendMailController
    participant SMTP as SMTP Server
    participant DB as Database

    UI->>Prep: User clicks "Start Sending"
    Prep->>Prep: Prepare email data
    Prep->>Coord: start_sending(info)
    Coord->>Bus: publish("start_sending", info)
    Bus->>Ctrl: start_sending(info)
    Ctrl->>Ctrl: Validate email provider
    Ctrl->>SMTP: Connect & Login
    SMTP-->>Ctrl: Connection established
    
    loop For each recipient
        Ctrl->>Ctrl: Format email body
        Ctrl->>SMTP: Send email
        SMTP-->>Ctrl: Email sent
        Ctrl->>DB: Log to SendLog
        Ctrl->>Bus: publish("log", message)
        Bus->>Coord: _on_log_received(message)
        Coord->>UI: display_log(message)
        Ctrl->>Ctrl: Wait 4.5-5.5 minutes
    end
    
    Ctrl->>SMTP: Quit connection
    Ctrl->>Bus: publish("log", "All emails sent")
    Bus->>Coord: _on_log_received("All emails sent")
    Coord->>UI: display_log("All emails sent")
```

### API Request Flow (Mermaid)

```mermaid
sequenceDiagram
    participant Client as Client App
    participant API as FastAPI App
    participant Router as API Router
    participant Schema as Pydantic Schema
    participant DB as Database Session
    participant ORM as SQLAlchemy ORM
    participant PG as PostgreSQL

    Client->>API: HTTP POST /api/email-templates/
    API->>Router: Route to email_templates.py
    Router->>Schema: Validate EmailTemplateCreate
    Schema-->>Router: Validated data
    Router->>DB: get_db() dependency
    DB-->>Router: Session object
    Router->>ORM: Create EmailTemplate instance
    Router->>DB: db.add(db_template)
    Router->>DB: db.commit()
    DB->>ORM: Execute INSERT
    ORM->>PG: SQL INSERT statement
    PG-->>ORM: Success response
    ORM-->>DB: Commit transaction
    DB-->>Router: Template created
    Router->>Schema: Convert to EmailTemplateResponse
    Schema-->>Router: Response model
    Router-->>API: JSON response
    API-->>Client: HTTP 200 + JSON
```

### Dashboard Data Loading (Mermaid)

```mermaid
sequenceDiagram
    participant UI as MyWindow
    participant Dash as Dashboard
    participant Model as Dashboard_model
    participant DB as PostgreSQL
    participant API as FastAPI (Future)

    UI->>Dash: __init__(widget)
    UI->>Dash: report()
    Dash->>Model: analysis_email("main_mail")
    Model->>DB: SELECT COUNT(...) FROM email_report
    DB-->>Model: Count result
    Model-->>Dash: Data
    Dash->>Dash: Update UI labels
    
    UI->>Dash: chart_email_answered_by_professor()
    Dash->>Model: Query answered emails
    Model->>DB: SELECT ... WHERE contact_status = 3
    DB-->>Model: Results
    Model-->>Dash: Data
    Dash->>Dash: Create pie chart
    
    Note over API: Future: Replace direct DB<br/>access with API calls
    UI->>API: GET /api/dashboard/stats/{email}
    API-->>UI: DashboardStats JSON
```

---

## Component Diagram

### System Architecture (Mermaid)

```mermaid
graph TB
    subgraph "Presentation Layer"
        UI[PyQt6 Desktop Application]
        UI_COMPONENTS[Dashboard<br/>EmailEditor<br/>ProfessorList<br/>Statics]
    end

    subgraph "Application Layer"
        CONTROLLERS[DashboardController<br/>ProfessorsController<br/>SendMailController]
        MIDDLEWARE[Coordinator<br/>middle_info_pass]
        EVENTS[EventBus]
    end

    subgraph "Data Access Layer (Legacy)"
        MODELS[Dashboard_model<br/>EmailTemplateModel<br/>connect_to_db]
    end

    subgraph "API Layer (New)"
        API[FastAPI Application]
        ROUTERS[Dashboard Router<br/>Templates Router<br/>Rules Router<br/>Queue Router]
        SCHEMAS[Pydantic Models]
    end

    subgraph "Database Layer"
        ORM[SQLAlchemy ORM Models]
        SESSION[Database Session]
        POSTGRES[(PostgreSQL Database)]
    end

    UI --> UI_COMPONENTS
    UI_COMPONENTS --> CONTROLLERS
    UI_COMPONENTS --> MIDDLEWARE
    CONTROLLERS --> EVENTS
    CONTROLLERS --> MODELS
    MIDDLEWARE --> EVENTS
    
    MODELS --> POSTGRES
    
    UI -.->|Future Integration| API
    API --> ROUTERS
    ROUTERS --> SCHEMAS
    ROUTERS --> SESSION
    SESSION --> ORM
    ORM --> POSTGRES
```

### Detailed Component Diagram (PlantUML)

```plantuml
@startuml Component Diagram
package "Presentation" {
    [PyQt6 Main Window] as MainUI
    [Dashboard View] as DashView
    [Email Editor] as EmailView
    [Professor List] as ProfView
    [Statistics View] as StatsView
}

package "Application Logic" {
    [Dashboard Controller] as DashCtrl
    [Professors Controller] as ProfCtrl
    [Send Mail Controller] as MailCtrl
    [Email Template Controller] as TempCtrl
}

package "Middleware" {
    [Coordinator] as Coord
    [Event Bus] as Bus
    [Info Pass] as Info
}

package "Data Models (Legacy)" {
    [Dashboard Model] as DashModel
    [Email Template Model] as TempModel
    [Database Connection] as DBConn
}

package "API Layer" {
    [FastAPI Main] as FastAPI
    [Dashboard Router] as DashRouter
    [Templates Router] as TempRouter
    [Rules Router] as RulesRouter
    [Queue Router] as QueueRouter
}

package "Schemas" {
    [Pydantic Models] as Schemas
}

package "Database" {
    [SQLAlchemy ORM] as ORM
    [PostgreSQL] as DB
}

MainUI --> DashView
MainUI --> EmailView
MainUI --> ProfView
MainUI --> StatsView

DashView --> DashCtrl
EmailView --> TempCtrl
ProfView --> ProfCtrl
EmailView --> MailCtrl

DashCtrl --> DashModel
TempCtrl --> TempModel
MailCtrl --> Coord
MailCtrl --> Bus

Coord --> Bus
Coord --> MailCtrl

DashModel --> DBConn
TempModel --> DBConn
DBConn --> DB

DashView -.-> DashRouter : Future
EmailView -.-> TempRouter : Future

FastAPI --> DashRouter
FastAPI --> TempRouter
FastAPI --> RulesRouter
FastAPI --> QueueRouter

DashRouter --> Schemas
TempRouter --> Schemas
RulesRouter --> Schemas
QueueRouter --> Schemas

DashRouter --> ORM
TempRouter --> ORM
RulesRouter --> ORM
QueueRouter --> ORM

ORM --> DB
@enduml
```

---

## Database Schema Details

### Core Tables

1. **users** - User accounts and authentication
2. **user_education_information** - Education details per user
3. **universities** - University master data
4. **departments** - Department master data
5. **professors** - Professor profiles
6. **professor_research_interests** - Research interests (many-to-many)
7. **open_positions** - Available positions/opportunities

### Email System Tables

8. **email_templates** - Email template storage
9. **template_files** - Files attached to templates
10. **sending_rules** - Email sending configuration
11. **email_queue** - Queue for scheduled emails
12. **send_log** - History of sent emails
13. **professor_contact** - Contact tracking

### Subscription Tables

14. **subscriptions** - Active subscriptions
15. **subscription_history** - Subscription history

### Review & Social Tables

16. **professor_review** - Reviews of professors
17. **comment** - Comments on reviews
18. **review_vote** - Votes on reviews
19. **comment_vote** - Votes on comments

### Utility Tables

20. **saved_positions** - User bookmarks
21. **chat_log** - Chatbot logs
22. **api_token** - API authentication tokens
23. **metric** - User metrics
24. **professor_list** - Uploaded professor lists
25. **email_property** - Email account properties
26. **file** - File registry

---

## API Endpoints Summary

### Dashboard Endpoints
- `GET /api/dashboard/stats/{user_email}` - Get dashboard statistics
- `GET /api/dashboard/email-analysis/{user_email}` - Get email analysis by type

### Email Templates Endpoints
- `POST /api/email-templates/` - Create template
- `GET /api/email-templates/{user_email}` - Get all templates
- `GET /api/email-templates/{user_email}/{template_id}` - Get specific template
- `PUT /api/email-templates/{template_id}` - Update template
- `DELETE /api/email-templates/{template_id}` - Delete template

### Sending Rules Endpoints
- `POST /api/sending-rules/` - Create rules
- `GET /api/sending-rules/{user_email}` - Get rules
- `PUT /api/sending-rules/{rules_id}` - Update rules

### Email Queue Endpoints
- `POST /api/email-queue/` - Add to queue
- `GET /api/email-queue/{user_email}` - Get queue items
- `GET /api/email-queue/send-logs/{user_email}` - Get send logs

---

## Notes

1. **Legacy Code**: The existing PyQt6 application uses direct database connections via `psycopg`. The FastAPI layer provides a modern REST API alternative.

2. **Future Migration**: The UI components can gradually migrate from direct database access to API calls.

3. **Event-Driven Architecture**: The email sending system uses an event bus pattern for decoupled communication.

4. **ORM Benefits**: SQLAlchemy ORM provides type safety, relationship management, and easier maintenance compared to raw SQL.

5. **API Documentation**: FastAPI automatically generates OpenAPI/Swagger documentation at `/docs` endpoint.

---

## Diagram Tools

- **Mermaid**: Supported by GitHub, GitLab, and many markdown viewers
- **PlantUML**: Requires PlantUML plugin or online viewer (http://www.plantuml.com/plantuml/uml/)

To view PlantUML diagrams, use:
- VS Code: Install "PlantUML" extension
- Online: http://www.plantuml.com/plantuml/uml/
- Local: Install PlantUML Java application

---

**Last Updated**: 2025-01-16
**Version**: 1.0.0

