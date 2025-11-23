# Migration to SQLAlchemy ORM

## Summary

The database schema in `DB/drawSQL-pgsql-export-2025-11-16.sql` has been successfully converted to SQLAlchemy ORM models.

## What Was Done

### 1. Created ORM Models (`api/db_models.py`)

All 25+ database tables have been converted to SQLAlchemy ORM models:

- **User & Authentication**: User, UserEducationInformation
- **Universities**: University, Department
- **Professors**: Professor, ProfessorResearchInterest, OpenPosition
- **Contacts**: ProfessorContact, SavedPosition
- **Email System**: EmailTemplate, TemplateFile, SendingRules, EmailQueue, SendLog
- **Reviews**: ProfessorReview, Comment, ReviewVote, CommentVote
- **Subscriptions**: Subscription, SubscriptionHistory
- **Utilities**: ChatLog, APIToken, Metric, ProfessorList, EmailProperty, File

### 2. Updated Database Connection (`api/database.py`)

- Replaced `psycopg` direct connections with SQLAlchemy engine
- Created session factory (`SessionLocal`)
- Added `get_db()` dependency function for FastAPI
- Added `get_db_session()` context manager

### 3. Updated API Routes

All routes now use ORM instead of raw SQL:

- **dashboard.py**: Uses `db.query(SendLog)`, `db.query(ProfessorContact)`, etc.
- **email_templates.py**: Uses `EmailTemplate` model for CRUD operations
- **sending_rules.py**: Uses `SendingRules` model for CRUD operations
- **email_queue.py**: Uses `EmailQueue` and `SendLog` models

### 4. Updated Dependencies (`requirements.txt`)

Added:
- `sqlalchemy==2.0.23`
- `alembic==1.12.1` (for future migrations)

## Key Features

### Relationships

All foreign key relationships are properly defined:
```python
# Example: User has many EmailTemplates
email_templates = relationship('EmailTemplate', back_populates='user', cascade='all, delete-orphan')
```

### Indexes

All database indexes are preserved:
```python
__table_args__ = (
    Index('idx_users_created_at', 'created_at'),
)
```

### Constraints

- Unique constraints: `UniqueConstraint('user_email', 'position_id')`
- Check constraints: `CheckConstraint("email <> ''")`
- Foreign keys: `ForeignKey('users.email', ondelete='CASCADE')`

## Usage Examples

### Querying Data

**Before (Raw SQL):**
```python
cur.execute("SELECT * FROM email_templates WHERE user_email = %s", (user_email,))
results = cur.fetchall()
```

**After (ORM):**
```python
templates = db.query(EmailTemplate).filter(
    EmailTemplate.user_email == user_email
).all()
```

### Creating Records

**Before:**
```python
cur.execute("INSERT INTO email_templates (...) VALUES (...)", values)
conn.commit()
```

**After:**
```python
template = EmailTemplate(user_email=email, template_body=body, ...)
db.add(template)
db.commit()
```

### Updating Records

**Before:**
```python
cur.execute("UPDATE email_templates SET template_body = %s WHERE id = %s", (body, id))
conn.commit()
```

**After:**
```python
template = db.query(EmailTemplate).filter(EmailTemplate.id == id).first()
template.template_body = body
db.commit()
```

## Benefits

1. **Type Safety**: SQLAlchemy provides type hints and validation
2. **Readability**: More Pythonic and readable code
3. **Maintainability**: Easier to modify and extend
4. **Relationships**: Automatic handling of relationships
5. **Less SQL**: No need to write raw SQL queries
6. **Migration Ready**: Can use Alembic for database migrations
7. **Better Errors**: More descriptive error messages

## Next Steps

1. **Test the API**: Run the FastAPI server and test all endpoints
2. **Add Alembic**: Set up Alembic for database migrations
3. **Add Validation**: Add SQLAlchemy validators for data validation
4. **Add Business Logic**: Add model methods for business logic
5. **Performance**: Consider adding query optimization and caching

## Files Changed

- ✅ `api/db_models.py` - Created (new file)
- ✅ `api/database.py` - Updated to use SQLAlchemy
- ✅ `api/routes/dashboard.py` - Updated to use ORM
- ✅ `api/routes/email_templates.py` - Updated to use ORM
- ✅ `api/routes/sending_rules.py` - Updated to use ORM
- ✅ `api/routes/email_queue.py` - Updated to use ORM
- ✅ `requirements.txt` - Added SQLAlchemy dependencies
- ✅ `README_ORM.md` - Created documentation

## Testing

To test the ORM models:

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the API server:
   ```bash
   python start_api.py
   ```

3. Test endpoints:
   - Visit http://localhost:8000/docs for Swagger UI
   - Test dashboard stats: `GET /api/dashboard/stats/{user_email}`
   - Test email templates: `GET /api/email-templates/{user_email}`

## Notes

- The database connection uses `postgresql+psycopg://` driver
- All models use the same table names as the original schema
- Relationships are bidirectional where appropriate
- Cascade deletes are configured for parent-child relationships
- The `Base.metadata.create_all()` is commented out (use Alembic for migrations)


