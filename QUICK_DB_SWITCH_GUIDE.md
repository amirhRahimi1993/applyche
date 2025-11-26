# Quick Database Configuration Switch Guide

## Overview

The API automatically reads database configuration from `model/server_info.env`. To switch between local and remote databases, simply update this file.

## Quick Switch Methods

### Method 1: Use the Helper Script (Recommended)

```bash
# Interactive mode
python switch_db_config.py

# Command line mode
python switch_db_config.py local    # Switch to local
python switch_db_config.py remote   # Switch to remote template
python switch_db_config.py show     # Show current config
python switch_db_config.py test     # Test connection
```

### Method 2: Manual Edit

Edit `model/server_info.env` directly:

**For Local PostgreSQL 18:**
```env
DB_USER=postgres
DB_PASS=applyche
DB_HOST=localhost
DB_PORT=5434
DB_NAME=applyche_global
```

**For Remote Server:**
```env
DB_USER=your_username
DB_PASS=your_password
DB_HOST=your_server_ip_or_domain
DB_PORT=5432
DB_NAME=applyche_global
```

## Configuration Files

All these files automatically read from `model/server_info.env`:

1. ✅ **`api/database.py`** - FastAPI SQLAlchemy connection
2. ✅ **`model/connect_db.py`** - Legacy database connection
3. ✅ **`model/dashboard_model.py`** - Dashboard database connection

**No code changes needed!** Just update the config file.

## Testing Connection

### Test via Script
```bash
python switch_db_config.py test
```

### Test via API
```bash
# Start API server
python -m uvicorn api.main:app --reload

# Test health endpoint
curl http://localhost:8000/health
```

### Test via Python
```python
from api.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT version();"))
    print(result.fetchone()[0])
```

## Common Scenarios

### Scenario 1: Development (Local)
```env
DB_HOST=localhost
DB_PORT=5434
DB_USER=postgres
DB_PASS=applyche
```

### Scenario 2: Production (Remote Server)
```env
DB_HOST=192.168.1.100
DB_PORT=5432
DB_USER=prod_user
DB_PASS=secure_password
```

### Scenario 3: Cloud Database (AWS RDS, DigitalOcean, etc.)
```env
DB_HOST=your-db-instance.region.rds.amazonaws.com
DB_PORT=5432
DB_USER=admin
DB_PASS=your_cloud_password
```

## Backup and Restore

The helper script automatically creates backups:

```bash
# Backup is created automatically when switching
# Restore from backup:
python switch_db_config.py restore
```

Or manually:
```bash
# Backup
cp model/server_info.env model/server_info.env.backup

# Restore
cp model/server_info.env.backup model/server_info.env
```

## Verification

After changing configuration:

1. **Check configuration:**
   ```bash
   python switch_db_config.py show
   ```

2. **Test connection:**
   ```bash
   python switch_db_config.py test
   ```

3. **Start API and verify:**
   ```bash
   python -m uvicorn api.main:app --reload
   # Visit http://localhost:8000/health
   ```

## Troubleshooting

### Connection Refused
- Check PostgreSQL is running
- Verify port number is correct
- Check firewall settings

### Authentication Failed
- Verify username and password
- Check PostgreSQL `pg_hba.conf` allows connections

### Database Not Found
- Ensure database exists: `CREATE DATABASE applyche_global;`
- Or update `DB_NAME` in config

## Security Notes

⚠️ **Important:**
- `model/server_info.env` is in `.gitignore` (not committed to git)
- Never commit passwords to version control
- Use strong passwords for production
- Consider using environment variables for production deployments

## Summary

✅ **One file controls everything:** `model/server_info.env`  
✅ **No code changes needed** when switching databases  
✅ **Helper script available:** `switch_db_config.py`  
✅ **Automatic backups** when using helper script  
✅ **Easy testing** with built-in test command  

For detailed information, see `DATABASE_CONFIGURATION.md`.


