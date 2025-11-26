# Database Configuration Guide

## Overview

The ApplyChe application uses PostgreSQL 18 as its database. All database connection settings are centralized in `model/server_info.env` for easy configuration and flexibility.

## Default Configuration

**PostgreSQL 18 on Localhost:**
- **Host**: localhost
- **Port**: 5434 (PostgreSQL 18 default)
- **User**: postgres
- **Password**: applyche
- **Database**: applyche_global

## Configuration File

All database connections read from `model/server_info.env`:

```env
DB_USER=postgres
DB_PASS=applyche
DB_HOST=localhost
DB_PORT=5434
DB_NAME=applyche_global
```

## Files Using Database Configuration

The following files automatically read from `model/server_info.env`:

1. **`api/database.py`** - FastAPI SQLAlchemy connection
   - Used by: All API routes
   - Connection pooling: QueuePool (10 connections, max 30)
   - Driver: `postgresql+psycopg://`

2. **`model/connect_db.py`** - Legacy database connection
   - Used by: Legacy controllers and models
   - Driver: `psycopg` (psycopg3)

3. **`model/dashboard_model.py`** - Dashboard database connection
   - Used by: Dashboard statistics
   - Driver: `psycopg` (psycopg3)

4. **`model/email_format.py`** - Email format database connection
   - Uses: `connect_to_db` from `model/connect_db.py`
   - Inherits configuration automatically

## Default Values

All connection files have sensible defaults if environment variables are not set:

```python
DB_NAME = os.getenv("DB_NAME", "applyche_global")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "applyche")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5434"))  # PostgreSQL 18 default
```

## Connecting to Remote Server

To connect to a remote PostgreSQL server:

### 1. Update `model/server_info.env`:

```env
DB_USER=your_username
DB_PASS=your_password
DB_HOST=your_server_ip_or_domain
DB_PORT=5432
DB_NAME=applyche_global
```

### 2. Common Remote Server Configurations:

**AWS RDS:**
```env
DB_USER=admin
DB_PASS=your_rds_password
DB_HOST=your-rds-instance.region.rds.amazonaws.com
DB_PORT=5432
DB_NAME=applyche_global
```

**DigitalOcean Managed Database:**
```env
DB_USER=doadmin
DB_PASS=your_do_password
DB_HOST=your-db-host.db.ondigitalocean.com
DB_PORT=25060
DB_NAME=applyche_global
```

**Custom VPS/Server:**
```env
DB_USER=postgres
DB_PASS=your_secure_password
DB_HOST=192.168.1.100
DB_PORT=5432
DB_NAME=applyche_global
```

### 3. PostgreSQL Server Configuration

For remote connections, ensure your PostgreSQL server is configured:

**`postgresql.conf`:**
```conf
listen_addresses = '*'  # or specific IP addresses
port = 5432  # or your configured port
```

**`pg_hba.conf`:**
```
# Allow connections from your application server
host    all             all             YOUR_APP_IP/32           md5
# Or for specific database
host    applyche_global all             YOUR_APP_IP/32           md5
```

### 4. Firewall Configuration

Ensure the database port is open:
- **Linux (ufw)**: `sudo ufw allow 5432/tcp`
- **Windows Firewall**: Add inbound rule for PostgreSQL port
- **Cloud Providers**: Configure security groups/firewall rules

## Connection Pooling (FastAPI)

The FastAPI application uses connection pooling for better performance:

```python
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,        # Maintain 10 connections
    max_overflow=20,      # Allow up to 30 total connections
    pool_pre_ping=True,   # Verify connections before use
    pool_recycle=3600,    # Recycle connections after 1 hour
)
```

**For Production:**
- Adjust `pool_size` based on expected concurrent requests
- `max_overflow` should be 2-3x `pool_size` for burst traffic
- `pool_recycle` prevents stale connections

## SSL/TLS Configuration

### For Remote Connections (Recommended)

Update connection files to require SSL:

**`api/database.py`:**
```python
DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
```

**`model/connect_db.py` and `model/dashboard_model.py`:**
```python
self.conn = psycopg.connect(
    dbname=self.db_name,
    user=self.username,
    password=self.password,
    host=self.host,
    port=self.port,
    sslmode="require"  # Changed from "prefer"
)
```

### SSL Modes:
- `disable` - No SSL
- `allow` - Try SSL, fallback to non-SSL
- `prefer` - Prefer SSL, fallback to non-SSL (default)
- `require` - Require SSL (recommended for remote)
- `verify-ca` - Require SSL and verify CA
- `verify-full` - Require SSL, verify CA and hostname

## Testing Connection

### 1. Test from Python:

```python
from api.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT version();"))
    print(result.fetchone())
```

### 2. Test from Command Line:

```bash
# Using psql
psql -h localhost -p 5434 -U postgres -d applyche_global

# Using connection string
psql "postgresql://postgres:applyche@localhost:5434/applyche_global"
```

### 3. Test API Health Endpoint:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

## Troubleshooting

### Connection Refused

**Error**: `[WinError 10061] No connection could be made because the target machine actively refused it`

**Solutions:**
1. Verify PostgreSQL is running: `pg_isready -h localhost -p 5434`
2. Check port in `model/server_info.env` matches PostgreSQL port
3. Verify firewall allows connections
4. For remote: Check `listen_addresses` in `postgresql.conf`

### Authentication Failed

**Error**: `password authentication failed for user`

**Solutions:**
1. Verify username and password in `model/server_info.env`
2. Check `pg_hba.conf` allows connections from your IP
3. Reset PostgreSQL password if needed:
   ```sql
   ALTER USER postgres WITH PASSWORD 'applyche';
   ```

### Database Does Not Exist

**Error**: `database "applyche_global" does not exist`

**Solutions:**
1. Create database:
   ```sql
   CREATE DATABASE applyche_global;
   ```
2. Or update `DB_NAME` in `model/server_info.env` to existing database

### Connection Timeout

**Error**: `timeout expired` or `connection timed out`

**Solutions:**
1. Check network connectivity to database server
2. Verify firewall rules allow connections
3. Check PostgreSQL is listening on correct interface
4. For remote: Verify security groups/firewall rules

### Too Many Connections

**Error**: `remaining connection slots are reserved`

**Solutions:**
1. Increase `max_connections` in `postgresql.conf`
2. Reduce `pool_size` and `max_overflow` in `api/database.py`
3. Close unused connections
4. Check for connection leaks in application code

## Environment Variables

You can also set database configuration via environment variables (takes precedence over `.env` file):

```bash
# Linux/Mac
export DB_USER=postgres
export DB_PASS=applyche
export DB_HOST=localhost
export DB_PORT=5434
export DB_NAME=applyche_global

# Windows (PowerShell)
$env:DB_USER="postgres"
$env:DB_PASS="applyche"
$env:DB_HOST="localhost"
$env:DB_PORT="5434"
$env:DB_NAME="applyche_global"
```

## Security Best Practices

1. **Never commit `server_info.env`** - Already in `.gitignore`
2. **Use strong passwords** - Especially for production
3. **Enable SSL** - For all remote connections
4. **Limit access** - Use `pg_hba.conf` to restrict connections
5. **Use environment variables** - For production deployments
6. **Rotate credentials** - Regularly change database passwords
7. **Monitor connections** - Check for suspicious activity

## Migration Notes

### From PostgreSQL 15/16 to PostgreSQL 18

PostgreSQL 18 uses port 5434 by default (instead of 5432). Update your configuration:

```env
DB_PORT=5434  # Changed from 5432
```

### From Hardcoded Ports to Configuration

All hardcoded ports (5433) have been replaced with configurable settings:
- ✅ `api/database.py` - Now reads `DB_PORT` from env
- ✅ `model/connect_db.py` - Now reads `DB_PORT` from env
- ✅ `model/dashboard_model.py` - Now reads `DB_PORT` from env

## Summary

- **Configuration File**: `model/server_info.env`
- **Default Port**: 5434 (PostgreSQL 18)
- **Default Host**: localhost
- **Flexible**: Easy to switch between local and remote servers
- **Secure**: Supports SSL/TLS for remote connections
- **Pooled**: FastAPI uses connection pooling for performance

For questions or issues, refer to the troubleshooting section above.


