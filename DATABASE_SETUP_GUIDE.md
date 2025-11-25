# Database Setup Guide

## Quick Setup

The database `applyche_global` does not exist. Run the setup script to create it:

```bash
python setup_database.py
```

This script will:
1. ✅ Connect to PostgreSQL server
2. ✅ Create the `applyche_global` database if it doesn't exist
3. ✅ Optionally initialize the schema from SQL file
4. ✅ Test the connection

## Manual Setup

If you prefer to set up the database manually:

### Step 1: Connect to PostgreSQL

```bash
# Using psql command line
psql -h localhost -p 5434 -U postgres

# Or using connection string
psql "postgresql://postgres:applyche@localhost:5434/postgres"
```

### Step 2: Create Database

```sql
CREATE DATABASE applyche_global;
```

### Step 3: Initialize Schema

```bash
# Using psql
psql -h localhost -p 5434 -U postgres -d applyche_global -f DB/drawSQL-pgsql-export-2025-11-16.sql

# Or connect and run
psql -h localhost -p 5434 -U postgres -d applyche_global
\i DB/drawSQL-pgsql-export-2025-11-16.sql
```

## Verify Setup

After setup, test the connection:

```bash
python switch_db_config.py test
```

Or test via API:

```bash
# Start API server
python -m uvicorn api.main:app --reload

# Test health endpoint
curl http://localhost:8000/health
```

## Troubleshooting

### Database Already Exists

If the database already exists, the setup script will skip creation and just test the connection.

### Permission Denied

If you get permission errors:
```sql
-- Grant permissions (run as postgres superuser)
GRANT ALL PRIVILEGES ON DATABASE applyche_global TO postgres;
```

### Connection Refused

If connection is refused:
- Check PostgreSQL is running: `pg_isready -h localhost -p 5434`
- Verify port in `model/server_info.env` matches PostgreSQL port
- Check firewall settings

### Schema Already Initialized

If tables already exist, the schema initialization will skip existing objects (safe to run multiple times).

## Next Steps

After database setup:
1. ✅ Start FastAPI server: `python -m uvicorn api.main:app --reload`
2. ✅ Test API: Visit http://localhost:8000/docs
3. ✅ Run PyQt6 app: `python view/main_ui.py`

## Configuration

Database settings are in `model/server_info.env`:
```
DB_USER=postgres
DB_PASS=applyche
DB_HOST=localhost
DB_PORT=5434
DB_NAME=applyche_global
```

See `DATABASE_CONFIGURATION.md` for detailed configuration options.

