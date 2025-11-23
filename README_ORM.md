# SQLAlchemy ORM Models

This document describes the SQLAlchemy ORM models that have been created to replace direct database queries.

## Overview

All database tables from `DB/drawSQL-pgsql-export-2025-11-16.sql` have been converted to SQLAlchemy ORM models in `api/db_models.py`.

## Models Created

### Core Models

1. **User** - User accounts and authentication
2. **UserEducationInformation** - User education details
3. **University** - University information
4. **Department** - Department information
5. **Professor** - Professor profiles
6. **ProfessorResearchInterest** - Research interests for professors
7. **OpenPosition** - Open positions/opportunities
8. **ProfessorContact** - Contact tracking between users and professors
9. **SavedPosition** - User bookmarks for positions

### Email & Communication Models

10. **EmailTemplate** - Email templates
11. **TemplateFile** - Files attached to templates
12. **SendingRules** - Email sending configuration
13. **EmailQueue** - Email queue for sending
14. **SendLog** - Log of sent emails

### Review & Social Models

15. **ProfessorReview** - Reviews of professors
16. **Comment** - Comments on reviews
17. **ReviewVote** - Votes on reviews
18. **CommentVote** - Votes on comments

### Subscription & Premium Models

19. **Subscription** - Active subscriptions
20. **SubscriptionHistory** - Subscription history

### Utility Models

21. **ChatLog** - Chatbot interaction logs
22. **APIToken** - API authentication tokens
23. **Metric** - User metrics and statistics
24. **ProfessorList** - User-uploaded professor lists
25. **EmailProperty** - Email account properties
26. **File** - Generic file registry

## Database Connection

The database connection has been updated to use SQLAlchemy:

- **File**: `api/database.py`
- **Engine**: SQLAlchemy engine with PostgreSQL
- **Session**: SQLAlchemy session factory
- **Dependency**: `get_db()` function for FastAPI dependency injection

## Updated Routes

All API routes have been updated to use ORM instead of raw SQL:

- `api/routes/dashboard.py` - Uses ORM queries
- `api/routes/email_templates.py` - Uses ORM CRUD operations
- `api/routes/sending_rules.py` - Uses ORM CRUD operations
- `api/routes/email_queue.py` - Uses ORM queries

## Usage Example

```python
from api.database import get_db
from api.db_models import EmailTemplate
from sqlalchemy.orm import Session

# In a FastAPI route
@router.get("/templates")
async def get_templates(user_email: str, db: Session = Depends(get_db)):
    templates = db.query(EmailTemplate).filter(
        EmailTemplate.user_email == user_email
    ).all()
    return templates
```

## Relationships

All foreign key relationships are properly defined with:
- `relationship()` for SQLAlchemy relationships
- Proper cascade options (`cascade='all, delete-orphan'`)
- Back references for bidirectional relationships

## Indexes

All database indexes are preserved in the ORM models using `Index()` in `__table_args__`.

## Constraints

- Unique constraints using `UniqueConstraint()`
- Check constraints using `CheckConstraint()`
- Foreign key constraints via `ForeignKey()`

## Benefits

1. **Type Safety**: SQLAlchemy provides type hints and validation
2. **Query Builder**: More readable and maintainable queries
3. **Relationship Management**: Automatic handling of relationships
4. **Migration Support**: Ready for Alembic migrations
5. **Less SQL**: No need to write raw SQL queries
6. **Better Error Handling**: SQLAlchemy provides better error messages

## Next Steps

1. Consider using Alembic for database migrations
2. Add validation at the model level using SQLAlchemy validators
3. Add hybrid properties for computed fields
4. Consider adding model-level business logic methods


