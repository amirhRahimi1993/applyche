"""
Database setup script for ApplyChe
Creates the database and initializes it with the schema
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv("model/server_info.env")

# Database configuration
DB_NAME = os.getenv("DB_NAME", "applyche_global")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "applyche")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5434"))

try:
    import psycopg
except ImportError:
    print("Error: psycopg is not installed. Please install it:")
    print("  pip install psycopg[binary]")
    sys.exit(1)


def create_database():
    """Create the database if it doesn't exist"""
    print("=" * 60)
    print("ApplyChe Database Setup")
    print("=" * 60)
    print(f"\nConnecting to PostgreSQL server:")
    print(f"  Host: {DB_HOST}")
    print(f"  Port: {DB_PORT}")
    print(f"  User: {DB_USER}")
    print(f"  Database: {DB_NAME}")
    print()
    
    try:
        # Connect to PostgreSQL server (not to the specific database)
        # Use 'postgres' database which should always exist
        print("Step 1: Connecting to PostgreSQL server...")
        conn = psycopg.connect(
            dbname="postgres",  # Connect to default database
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.autocommit = True
        print("✓ Connected to PostgreSQL server")
        
        # Check if database exists
        print(f"\nStep 2: Checking if database '{DB_NAME}' exists...")
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (DB_NAME,)
        )
        exists = cur.fetchone()
        
        if exists:
            print(f"✓ Database '{DB_NAME}' already exists")
            cur.close()
            conn.close()
            return True
        else:
            # Create database
            print(f"\nStep 3: Creating database '{DB_NAME}'...")
            cur.execute(f'CREATE DATABASE "{DB_NAME}"')
            print(f"✓ Database '{DB_NAME}' created successfully")
            cur.close()
            conn.close()
            return True
            
    except psycopg.OperationalError as e:
        print(f"\n✗ Connection failed: {e}")
        print("\nPlease check:")
        print(f"  1. PostgreSQL is running on {DB_HOST}:{DB_PORT}")
        print(f"  2. Username '{DB_USER}' and password are correct")
        print(f"  3. PostgreSQL server is accessible")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False


def initialize_schema():
    """Initialize database schema from SQL file"""
    sql_file = Path("DB/drawSQL-pgsql-export-2025-11-16.sql")
    
    if not sql_file.exists():
        print(f"\n⚠️  SQL schema file not found: {sql_file}")
        print("   Database created but schema not initialized.")
        print("   You can manually run the SQL file to create tables.")
        return False
    
    print(f"\nStep 4: Initializing database schema from {sql_file}...")
    try:
        # Connect to the new database
        conn = psycopg.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # Read and execute SQL file
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Split by semicolons and execute each statement
        # Skip comments and empty statements
        statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]
        
        executed = 0
        for statement in statements:
            if statement:
                try:
                    cur.execute(statement)
                    executed += 1
                except Exception as e:
                    # Some statements might fail (like CREATE EXTENSION IF NOT EXISTS)
                    # which is fine if they already exist
                    if "already exists" not in str(e).lower():
                        print(f"   Warning: {str(e)[:100]}")
        
        cur.close()
        conn.close()
        print(f"✓ Schema initialized ({executed} statements executed)")
        return True
        
    except Exception as e:
        print(f"✗ Error initializing schema: {e}")
        print("   You may need to manually run the SQL file.")
        return False


def test_connection():
    """Test connection to the database"""
    print(f"\nStep 5: Testing connection to '{DB_NAME}'...")
    try:
        conn = psycopg.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        print(f"✓ Connection successful!")
        print(f"  PostgreSQL Version: {version.split(',')[0]}")
        
        # Check if tables exist
        cur.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        table_count = cur.fetchone()[0]
        print(f"  Tables in database: {table_count}")
        
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"✗ Connection test failed: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("ApplyChe Database Setup")
    print("=" * 60)
    
    # Create database
    if not create_database():
        print("\n✗ Database setup failed. Please fix the errors above.")
        sys.exit(1)
    
    # Initialize schema (optional - user can skip this)
    print("\n" + "-" * 60)
    response = input("\nDo you want to initialize the database schema from SQL file? (y/n): ").strip().lower()
    if response == 'y':
        initialize_schema()
    else:
        print("   Skipping schema initialization.")
        print("   You can run the SQL file manually later.")
    
    # Test connection
    if test_connection():
        print("\n" + "=" * 60)
        print("✓ Database setup complete!")
        print("=" * 60)
        print("\nYou can now start the FastAPI server:")
        print("  python -m uvicorn api.main:app --reload")
        print()
    else:
        print("\n⚠️  Setup completed but connection test failed.")
        print("   Please verify your database configuration.")

