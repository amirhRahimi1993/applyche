# UML Diagrams Quick Reference

This is a quick reference guide for the UML diagrams in the ApplyChe project.

## 📊 Diagram Locations

| Diagram Type | Location | Format |
|-------------|----------|--------|
| **Main Documentation** | `UML_DOCUMENTATION.md` | Mermaid + Markdown |
| **Database ER Diagram** | `uml/database_er.puml` | PlantUML |
| **API Architecture** | `uml/api_architecture.puml` | PlantUML |
| **Class Diagrams** | `uml/class_diagram.puml` | PlantUML |
| **Sequence Diagrams** | `uml/sequence_diagrams.puml` | PlantUML |

## 🗄️ Database Schema (26 Tables)

### Core Tables
- `users` - User accounts
- `user_education_information` - Education details
- `universities` - University master data
- `departments` - Department master data
- `professors` - Professor profiles
- `professor_research_interests` - Research interests
- `open_positions` - Available positions

### Email System
- `email_templates` - Email templates
- `template_files` - Template attachments
- `sending_rules` - Sending configuration
- `email_queue` - Email queue
- `send_log` - Send history
- `professor_contact` - Contact tracking

### Subscriptions
- `subscriptions` - Active subscriptions
- `subscription_history` - Subscription history

### Reviews & Social
- `professor_review` - Reviews
- `comment` - Comments
- `review_vote` - Review votes
- `comment_vote` - Comment votes

### Utilities
- `saved_positions` - User bookmarks
- `chat_log` - Chatbot logs
- `api_token` - API tokens
- `metric` - User metrics
- `professor_list` - Uploaded lists
- `email_property` - Email properties
- `file` - File registry

## 🔌 API Endpoints

### Dashboard
- `GET /api/dashboard/stats/{user_email}` - Dashboard statistics
- `GET /api/dashboard/email-analysis/{user_email}` - Email analysis

### Email Templates
- `POST /api/email-templates/` - Create template
- `GET /api/email-templates/{user_email}` - Get all templates
- `GET /api/email-templates/{user_email}/{template_id}` - Get template
- `PUT /api/email-templates/{template_id}` - Update template
- `DELETE /api/email-templates/{template_id}` - Delete template

### Sending Rules
- `POST /api/sending-rules/` - Create rules
- `GET /api/sending-rules/{user_email}` - Get rules
- `PUT /api/sending-rules/{rules_id}` - Update rules

### Email Queue
- `POST /api/email-queue/` - Add to queue
- `GET /api/email-queue/{user_email}` - Get queue
- `GET /api/email-queue/send-logs/{user_email}` - Get logs

## 🏗️ Architecture Layers

### Presentation Layer
- `MyWindow` - Main PyQt6 window
- `Dashboard` - Dashboard view
- `EmailEditor` - Email template editor
- `Prepare_send_mail` - Email preparation
- `Professor_lists` - Professor list view
- `Statics` - Statistics view

### Controller Layer
- `DashboardController` - Dashboard logic
- `ProfessorsController` - Professor data handling
- `SendMailController` - Email sending logic
- `CheckPremium` - Premium check

### Model Layer (Legacy)
- `Dashboard_model` - Dashboard data access
- `EmailTemplateModel` - Template data access
- `connect_to_db` - Database connection

### Middleware
- `EventBus` - Event-driven communication
- `Coordinator` - Email sending coordination
- `middle_info_pass` - Data passing between components

### API Layer (New)
- `main.py` - FastAPI application
- Routers: `dashboard`, `email_templates`, `sending_rules`, `email_queue`
- Schemas: Pydantic models for validation
- ORM: SQLAlchemy models

## 🔄 Key Workflows

### Email Sending Flow
1. User clicks "Start Sending" in UI
2. `Prepare_send_mail` prepares data
3. `Coordinator` publishes event via `EventBus`
4. `SendMailController` handles sending
5. Connects to SMTP server
6. Sends emails with delays
7. Logs to database
8. Updates UI via events

### API Request Flow
1. Client sends HTTP request
2. FastAPI routes to appropriate router
3. Pydantic validates request
4. Router uses database session
5. SQLAlchemy ORM queries database
6. Response serialized via Pydantic
7. JSON response returned

### Dashboard Loading
1. `MyWindow` initializes `Dashboard`
2. `Dashboard` calls `Dashboard_model`
3. Model queries PostgreSQL directly
4. Data displayed in charts
5. **Future**: Replace with API calls

## 📝 Key Relationships

### User Relationships
- User → Email Templates (1:N)
- User → Sending Rules (1:1)
- User → Email Queue (1:N)
- User → Send Logs (1:N)
- User → Professor Contacts (1:N)
- User → Saved Positions (1:N)
- User → Reviews (1:N)

### Professor Relationships
- Professor → Research Interests (1:N)
- Professor → Open Positions (1:N)
- Professor → Contacts (1:N)
- Professor → Reviews (1:N)

### Email System Relationships
- Email Template → Template Files (1:N)
- Email Template → Email Queue (1:N)
- User → Sending Rules (1:1)
- Email Queue → Send Log (1:N)

## 🛠️ Tools for Viewing

### Mermaid Diagrams
- GitHub/GitLab: Renders automatically
- VS Code: Install "Markdown Preview Mermaid Support"
- Online: https://mermaid.live/

### PlantUML Diagrams
- VS Code: Install "PlantUML" extension
- Online: http://www.plantuml.com/plantuml/uml/
- IntelliJ/PyCharm: Built-in support
- Command line: Java + PlantUML JAR

## 📚 Additional Documentation

- **Main README**: `README.md` - Project overview
- **API Documentation**: `README_API.md` - API details
- **ORM Documentation**: `README_ORM.md` - ORM models
- **Migration Guide**: `MIGRATION_TO_ORM.md` - Migration details
- **Dependency Graph**: `DEPENDENCY_GRAPH.md` - File dependencies

## 🔍 Quick Search

### Find Database Table
→ See `UML_DOCUMENTATION.md` → Database ER Diagram

### Find API Endpoint
→ See `UML_DOCUMENTATION.md` → API Endpoints Summary

### Find Class Definition
→ See `uml/class_diagram.puml` or `UML_DOCUMENTATION.md` → Class Diagrams

### Understand Workflow
→ See `uml/sequence_diagrams.puml` or `UML_DOCUMENTATION.md` → Sequence Diagrams

### View Architecture
→ See `uml/api_architecture.puml` or `UML_DOCUMENTATION.md` → API Architecture Diagram

---

**Last Updated**: 2025-01-16  
**Version**: 1.0.0

