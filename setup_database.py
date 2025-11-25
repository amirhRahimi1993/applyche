"""
Database setup script for ApplyChe.
Creates the database and initializes it with the schema using SQLAlchemy ORM utilities.
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Load environment variables
load_dotenv("model/server_info.env")

# Database configuration
DB_NAME = os.getenv("DB_NAME", "applyche_global")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "applyche")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5434"))

ADMIN_DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/postgres"
TARGET_DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def create_database() -> bool:
    """Create the database if it does not already exist."""
    print("=" * 60)
    print("ApplyChe Database Setup")
    print("=" * 60)
    print(f"\nConnecting to PostgreSQL server:")
    print(f"  Host: {DB_HOST}")
    print(f"  Port: {DB_PORT}")
    print(f"  User: {DB_USER}")
    print(f"  Database: {DB_NAME}")
    print()

    admin_engine = create_engine(ADMIN_DATABASE_URL, isolation_level="AUTOCOMMIT", future=True)
    try:
        with admin_engine.connect() as conn:
            print("Step 1: Connecting to PostgreSQL server...")
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": DB_NAME},
            ).scalar()

            if exists:
                print(f"✓ Database '{DB_NAME}' already exists")
                return True

            print(f"\nStep 2: Creating database '{DB_NAME}'...")
            conn.execute(text(f'CREATE DATABASE "{DB_NAME}"'))
            print(f"✓ Database '{DB_NAME}' created successfully")
            return True
    except SQLAlchemyError as exc:
        print(f"\n✗ Connection failed: {exc}")
        print("\nPlease check:")
        print(f"  1. PostgreSQL is running on {DB_HOST}:{DB_PORT}")
        print(f"  2. Username '{DB_USER}' and password are correct")
        print(f"  3. PostgreSQL server is accessible")
        return False
    finally:
        admin_engine.dispose()


def initialize_schema() -> bool:
    """Initialize database schema from SQL file via SQLAlchemy."""
    sql_file = Path("DB/drawSQL-pgsql-export-2025-11-16.sql")

    if not sql_file.exists():
        print(f"\n⚠️  SQL schema file not found: {sql_file}")
        print("   Database created but schema not initialized.")
        print("   You can manually run the SQL file to create tables.")
        return False

    print(f"\nStep 3: Initializing database schema from {sql_file}...")
    target_engine = create_engine(TARGET_DATABASE_URL, future=True)
    try:
        with target_engine.connect() as conn:
            sql_content = sql_file.read_text(encoding="utf-8")
            statements = [
                stmt.strip()
                for stmt in sql_content.split(";")
                if stmt.strip() and not stmt.strip().startswith("--")
            ]

            executed = 0
            for statement in statements:
                try:
                    conn.execute(text(statement))
                    executed += 1
                except SQLAlchemyError as exc:
                    if "already exists" not in str(exc).lower():
                        print(f"   Warning: {str(exc)[:100]}")

            print(f"✓ Schema initialized ({executed} statements executed)")
            return True
    except SQLAlchemyError as exc:
        print(f"✗ Error initializing schema: {exc}")
        print("   You may need to manually run the SQL file.")
        return False
    finally:
        target_engine.dispose()


def test_connection() -> bool:
    """Test connection to the database."""
    print(f"\nStep 4: Testing connection to '{DB_NAME}'...")
    engine = create_engine(TARGET_DATABASE_URL, future=True)
    try:
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version();")).scalar()
            print("✓ Connection successful!")
            print(f"  PostgreSQL Version: {version.split(',')[0] if version else 'Unknown'}")

            table_count = conn.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    """
                )
            ).scalar()
            print(f"  Tables in database: {table_count}")
            return True
    except SQLAlchemyError as exc:
        print(f"✗ Connection test failed: {exc}")
        return False
    finally:
        engine.dispose()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("ApplyChe Database Setup")
    print("=" * 60)

    if not create_database():
        print("\n✗ Database setup failed. Please fix the errors above.")
        sys.exit(1)

    print("\n" + "-" * 60)
    response = input("\nDo you want to initialize the database schema from SQL file? (y/n): ").strip().lower()
    if response == "y":
        initialize_schema()
    else:
        print("   Skipping schema initialization.")
        print("   You can run the SQL file manually later.")

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

