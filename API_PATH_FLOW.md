## API Path Flow

This guide explains how each FastAPI route in `api/main.py` is wired, what data flows through it, and where it is used inside the ApplyChe desktop client and supporting scripts.

### 1. App & Router Overview

- Entry point: `api/main.py` bootstraps FastAPI, enables permissive CORS, and mounts five routers.
- Shared dependencies: every route pulls a SQLAlchemy `Session` from `api.database.get_db`, so ORM queries all run inside managed transactions.
- Client touchpoint: the PyQt6 app talks to the API exclusively through `ApplyCheAPIClient` (see `api_client.py`), which mirrors the endpoints below.

```
ApplyChe UI/Login → ApplyCheAPIClient → FastAPI route → SQLAlchemy ORM → PostgreSQL
```

### 2. Authentication Flow (`/api/auth/login`)

| Method | Path | Body | Response |
| ------ | ---- | ---- | -------- |
| POST | `/api/auth/login` | `LoginRequest { email, password }` | `LoginResponse { email, display_name, message }` |

1. `LoginDialog` collects credentials and calls `ApplyCheAPIClient.login()`.
2. `/api/auth/login` fetches the `User` row via SQLAlchemy.
3. `api.security.verify_password()` compares the submitted password to `users.password_hash`.
4. On success the route returns display metadata that the UI shows in the header; failures raise `401` or `403`.

### 3. Dashboard Flow (`/api/dashboard`)

- `GET /api/dashboard/stats/{user_email}`: Aggregates counts from `SendLog`, `ProfessorContact`, and `EmailQueue` using SQL-level `CASE` blocks. The Qt `Dashboard` class calls this endpoint to paint hero widgets and pie charts.
- `GET /api/dashboard/email-analysis/{user_email}?email_type=main_mail`: Returns counts for a single `send_type`. Used for drill-down charts or analytics panels.

Flow: PyQt dashboard → client `get_dashboard_stats()` → FastAPI route → aggregated ORM query → JSON stats payload.

### 4. Email Template Flow (`/api/email-templates`)

| Action | Endpoint | Notes |
| ------ | -------- | ----- |
| Create | `POST /api/email-templates/` | Accepts `EmailTemplateCreate`; optional `file_paths` query param stores attachments inside `TemplateFile`. Auto-creates a `User` row during development if missing. |
| List | `GET /api/email-templates/{user_email}` | Returns all templates with eager-loaded files. |
| Retrieve | `GET /api/email-templates/{user_email}/{template_id}` | Single template, `404` when missing. |
| Update | `PUT /api/email-templates/{template_id}?user_email=...&file_paths=...` | Replaces body/subject/type and rewrites associated `TemplateFile` rows. |
| Delete | `DELETE /api/email-templates/{template_id}?user_email=...` | Removes template + cascade files. |
| Latest-by-type | `GET /api/email-templates/{user_email}/by-type/{template_type}` | Returns newest template for a given type (0–3). |
| Batch lookup | `GET /api/email-templates/{user_email}/by-types?template_types=0,1,2,3` | Convenience endpoint the Qt editors use to hydrate all tabs with one call. |

Flow example (editing templates):

1. `EmailEditor` loads all template types via `get_templates_by_types`.
2. User edits HTML and clicks “Save”; the client calls `create_email_template` or `update_email_template`.
3. Route persists `EmailTemplate` + related `TemplateFile` records, then returns the canonical DTO so the UI can refresh IDs or attachment metadata.

### 5. Sending Rules Flow (`/api/sending-rules`)

| Method | Path | Purpose |
| ------ | ---- | ------- |
| POST | `/api/sending-rules/` | Idempotent “upsert”: creates the row if missing, otherwise updates all rule fields in one shot. |
| GET | `/api/sending-rules/{user_email}` | Fetches the rule set for pre-filling UI controls. |
| PATCH | `/api/sending-rules/{user_email}` | Partial update that only modifies provided attributes (e.g., just `max_email_per_university`). |

Flow: configuration UI → `ApplyCheAPIClient` → route → `SendingRules` ORM row. Responses serialize times as strings (e.g., `start_time_send`) for direct binding back into Qt line edits.

### 6. Email Queue & Send Log Flow (`/api/email-queue`)

| Action | Endpoint | Details |
| ------ | -------- | ------- |
| Enqueue email | `POST /api/email-queue/` | Creates `EmailQueue` row with status `0` (pending). Used by send-prep workflows when scheduling outreach. |
| List queue | `GET /api/email-queue/{user_email}?status=&limit=` | Filters by status (pending, sent, failed, retrying) and returns chronologically sorted items for dashboards or worker UIs. |
| Update status | `PATCH /api/email-queue/{queue_id}/status?user_email=&status=` | Marks queue items as sent/failed and stamps `last_attempt_at`. Intended for the background sender/coordinator. |
| Fetch logs | `GET /api/email-queue/logs/{user_email}?send_type=&limit=` | Reads from `SendLog` to drive history widgets and analytics. |

Flow example:

1. `Prepare_send_mail` gathers campaign data and calls the enqueue endpoint.
2. Worker processes poll `/api/email-queue/{user_email}` to send emails.
3. After each attempt they call the status endpoint and insert a `SendLog` row (handled inside `Coordinator` logic, not via a dedicated route yet).
4. Dashboards call the logs endpoint to visualize delivery results.

### 7. Supporting Endpoints

- `GET /` (root): Simple metadata object so uptime checks know the service/version.
- `GET /health`: Executes `SELECT 1` through the SQLAlchemy engine to confirm DB connectivity; useful for container orchestration probes.

### 8. Typical End-to-End Session

1. User launches the desktop app. `LoginDialog` sends credentials to `/api/auth/login`.
2. On success, `launch_main_window()` shows `MyWindow`. The dashboard immediately calls `/api/dashboard/stats/{user}` to draw charts.
3. Navigating to “Templates” triggers `/api/email-templates/{user}/by-types`, enabling inline edits that call `POST`/`PUT` routes as needed.
4. The “Sending Rules” panel saves settings via `POST /api/sending-rules/`.
5. When a campaign is scheduled, the UI calls `POST /api/email-queue/` for each recipient. Background tasks update queue statuses and logs, which keep the dashboard in sync.

Use this guide as a reference when adding new routes or integrating additional clients (CLI tools, web frontends). Each flow section mirrors the structure under `api/routes/`, so extending or debugging an endpoint is as simple as jumping to the corresponding file.

