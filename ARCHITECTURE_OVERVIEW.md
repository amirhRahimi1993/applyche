# ApplyChe Repository Architecture

This document gives newcomers a single place to understand how the project is structured, which components talk to each other, and how to extend or debug the system.

---

## 1. High-Level Picture

```
PyQt6 Desktop UI  <-->  ApplyChe API (FastAPI)  <-->  PostgreSQL 18
                     │
                     ├─ SQLAlchemy ORM models (`api/db_models.py`)
                     └─ Shared docs & scripts (UML, migration guides, setup helpers)
```

- **UI**: `view/main_ui.py` and supporting classes render the ApplyChe desktop interface.
- **API**: `api/main.py` boots FastAPI, wires routers, and exposes REST endpoints.
- **Database**: PostgreSQL 18 instance accessed exclusively through SQLAlchemy ORM sessions defined in `api/database.py`.

Everything shares configuration via `model/server_info.env`. Switching to a remote DB requires only updating that file or running `switch_db_config.py`.

---

## 2. Directory Cheat-Sheet

| Path                        | Purpose                                                                 |
|-----------------------------|-------------------------------------------------------------------------|
| `api/`                      | FastAPI app, routers, Pydantic schemas, SQLAlchemy models               |
| `view/`                     | PyQt6 UI (resizable components, API client integration)                 |
| `controller/`               | Thin wrappers for legacy UI logic (now ORM-backed)                      |
| `model/`                    | Legacy helper modules refactored to use SQLAlchemy sessions             |
| `DB/`                       | Original SQL export (`drawSQL-pgsql-export-2025-11-16.sql`)              |
| `uml/`                      | PlantUML diagrams (ERD, API, class, sequence)                           |
| `docs/*.md`                 | Detailed documentation (ORM migration, DB config, UML references, etc.) |
| `switch_db_config.py`       | Helper to toggle local/remote DB credentials                            |
| `setup_database.py`         | Creates the PostgreSQL database & applies schema using SQLAlchemy       |

---

## 3. Execution Flow

### 3.1 Application Startup
1. **API**: `python -m uvicorn api.main:app --reload`
   - Loads routers (`dashboard`, `email_templates`, `sending_rules`, `email_queue`)
   - Initializes SQLAlchemy engine with pooling.
2. **UI**: `python view/main_ui.py`
   - Instantiates `ApplyCheAPIClient`
   - Loads templates/resends data via API calls when the server is reachable.

### 3.2 Database Access
- `api/database.py` exposes:
  - `engine`
  - `SessionLocal`
  - `get_db()` dependency for FastAPI routes
  - `get_db_session()` context manager (for scripts/tests)
- All legacy modules (`model/*`, `controller/*`) now import `SessionLocal` instead of using raw psycopg connections.
- `setup_database.py` and `switch_db_config.py` use SQLAlchemy’s engine to manage databases.

---

## 4. Key Components

### FastAPI Routers (`api/routes/*.py`)
| Router              | Description                                                                         |
|---------------------|-------------------------------------------------------------------------------------|
| `dashboard.py`      | Aggregated stats for UI dashboard with optimized conditional aggregation queries    |
| `email_templates.py`| CRUD for email templates + attachment paths (`TemplateFile` relationship)           |
| `sending_rules.py`  | Manage per-user sending preferences                                                 |
| `email_queue.py`    | Queue items, send logs, status updates (UTC timestamps)                             |

### Pydantic Schemas (`api/models.py`)
- Request/response validation.
- `EmailTemplateResponse` now includes `file_paths` and mirrors ORM models.

### ORM Models (`api/db_models.py`)
- 26 tables converted from the original SQL export.
- Uses `DeclarativeBase` for SQLAlchemy 2.0+/Python 3.12 compatibility.
- Relationships set up with lazy-loading strategies that prevent N+1 queries (e.g., `joinedload`).

### PyQt6 UI (`view/main_ui.py`)
- `EmailEditor` reacts to window resizing, handles local persistence, and synchronizes with API when available.
- Button handlers call `save_template_data`, which now:
  - Shows friendly guidance if the API is offline.
  - Persists HTML bodies + file paths to the backend when online.
- `ApplyCheAPIClient` (in `api_client.py`) wraps REST calls with retries and a `is_available()` health check.

### Legacy Models/Controllers (Now ORM-Based)
- `model/connect_db.py`: returns a singleton with `.connect()` and `.session_scope()` methods that produce SQLAlchemy sessions.
- `model/dashboard_model.py`: executes the same aggregate queries as the FastAPI endpoint for older UI components.
- `model/email_format.py`: helper class (`EmailFormat`) manipulating `SendingRules`.
- `controller/dashboard_controller.py`: tiny wrapper calling `DashboardModel`.

---

## 5. Documentation Roadmap

Already available:
- `README.md`: setup steps, API usage, ORM sample insert, troubleshooting.
- `README_API.md`: API-specific instructions.
- `MIGRATION_TO_ORM.md`: exact steps taken during the ORM conversion.
- `DATABASE_CONFIGURATION.md` & `QUICK_DB_SWITCH_GUIDE.md`: environment management.
- `PERFORMANCE_OPTIMIZATIONS.md`, `API_CONNECTION_HANDLING.md`: rationale for recent fixes.
- `UML_DOCUMENTATION.md`, `uml/*.puml`: architecture visuals.
- `PYTHON_3.12_MIGRATION.md`: language/runtime upgrade notes.

This file (`ARCHITECTURE_OVERVIEW.md`) is the top-level narrative connecting all of the above.

---

## 6. How to Extend Safely

1. **Add new endpoints**:
   - Update/extend ORM models (`api/db_models.py`) if schema changes are needed.
   - Create/modify routers and Pydantic schemas.
   - Document behavior in `README.md` or dedicated docs.
2. **UI tweaks**:
   - Use existing controllers and API client functions.
   - Follow the resizing utilities already built into `view/main_ui.py`.
3. **Database changes**:
   - Modify ORM models.
   - Generate SQL migrations (Alembic ready in `requirements.txt`).
   - Update UML diagrams if structure changes.
4. **Configuration**:
   - Rely on `.env` values (no hardcoded credentials).
   - Run `switch_db_config.py test` after changes.

---

## 7. Quick Reference Links

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Sample ORM Insert**: section “Sample ORM Insert” in `README.md`
- **Database Creation**: `python setup_database.py`
- **Switch DB Config**: `python switch_db_config.py [local|remote|test|show]`
- **UML Viewer**: see `uml/README.md`

---

With this overview plus the existing doc set, a new contributor should be able to understand the entire stack, spin up the services, reason about data flow, and begin making changes confidently. For further details dive into `README.md` or the specific doc that matches your task.


