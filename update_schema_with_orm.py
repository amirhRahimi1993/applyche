"""
Update database schema using SQLAlchemy ORM metadata.create_all().

This script uses SQLAlchemy's Base.metadata.create_all() to automatically
create/update tables based on the ORM models.

WARNING: This will only ADD new columns/tables. It will NOT:
- Drop columns
- Modify existing column types
- Handle data migration

For production, use migrate_template_files_fk.py instead.

Usage:
    python update_schema_with_orm.py
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError

# Load environment variables
load_dotenv("model/server_info.env")

# Import database engine
from api.database import engine

# Import Base and all models to register them
# This ensures all tables are included in metadata.create_all()
from api.db_models import Base
import api.db_models  # Import module to register all models with Base

# Database configuration (for display)
DB_NAME = os.getenv("DB_NAME", "applyche_global")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5434"))


def update_schema():
    """Update database schema using ORM metadata"""
    print("=" * 60)
    print("Update Database Schema with ORM")
    print("=" * 60)
    print(f"\nDatabase: {DB_NAME}")
    print(f"Host: {DB_HOST}:{DB_PORT}\n")

    try:

        # Check connection
        print("Step 1: Testing database connection...")
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version();")).scalar()
            print(f"✓ Connected to PostgreSQL")
            print(f"  Version: {version.split(',')[0] if version else 'Unknown'}\n")

        # Create extension if needed
        print("Step 2: Ensuring CITEXT extension exists...")
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS citext"))
        print("✓ CITEXT extension ready\n")

        # Create/update all tables based on ORM models
        print("Step 3: Creating/updating tables from ORM models...")
        print("  This will:")
        print("    - Create new tables if they don't exist")
        print("    - Add new columns if they don't exist")
        print("    - NOT modify existing columns or drop columns")
        print()
        
        response = input("Continue? (y/n): ").strip().lower()
        if response != 'y':
            print("Cancelled.")
            return False

        Base.metadata.create_all(bind=engine, checkfirst=True)
        print("✓ Schema updated successfully!\n")

        # Explicitly add end_time_send column if it doesn't exist
        print("Step 4: Adding end_time_send column to sending_rules if needed...")
        inspector = inspect(engine)
        sending_rules_columns = [col['name'] for col in inspector.get_columns('sending_rules')]
        
        if 'end_time_send' not in sending_rules_columns:
            print("  Adding end_time_send column...")
            try:
                with engine.begin() as conn:
                    # Add the column with the same type as start_time_send
                    conn.execute(text("""
                        ALTER TABLE sending_rules 
                        ADD COLUMN IF NOT EXISTS end_time_send TIME WITH TIME ZONE
                    """))
                print("✓ end_time_send column added successfully")
            except SQLAlchemyError as e:
                print(f"⚠️  Error adding end_time_send column: {e}")
                print("   You may need to add it manually using:")
                print("   ALTER TABLE sending_rules ADD COLUMN end_time_send TIME WITH TIME ZONE;")
        else:
            print("✓ end_time_send column already exists")

        # Verify all required columns exist
        print("\nStep 5: Verifying sending_rules table structure...")
        inspector = inspect(engine)
        sending_rules_columns = [col['name'] for col in inspector.get_columns('sending_rules')]
        
        required_columns = ['end_time_send', 'local_professor_time', 'send_working_day_only']
        missing_columns = [col for col in required_columns if col not in sending_rules_columns]
        
        if not missing_columns:
            print("✓ All required columns exist in sending_rules:")
            for col in required_columns:
                print(f"    - {col}")
        else:
            print("⚠️  Missing columns in sending_rules:")
            for col in missing_columns:
                print(f"    - {col}")
            print("   Please add them manually using ALTER TABLE statements.")
            return False

        print("\n" + "=" * 60)
        print("✓ Schema update completed!")
        print("=" * 60)
        return True

    except SQLAlchemyError as exc:
        print(f"\n✗ Schema update failed: {exc}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        engine.dispose()


if __name__ == "__main__":
    success = update_schema()
    if not success:
        print("\n⚠️  Schema update did not complete successfully.")
        sys.exit(1)
    else:
        print("\n✅ Schema is up to date!")
        print("   Restart your FastAPI server to use the new schema.")

