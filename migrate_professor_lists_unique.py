"""
Migration script to add unique constraint on user_email in professor_lists table.

This ensures only one row per user exists in the professor_lists table.
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

DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def migrate_professor_lists():
    """Add unique constraint to professor_lists table"""
    print("=" * 60)
    print("Professor Lists Unique Constraint Migration")
    print("=" * 60)
    print(f"\nDatabase: {DB_NAME}")
    print(f"Host: {DB_HOST}:{DB_PORT}\n")

    engine = create_engine(DATABASE_URL, future=True)
    
    try:
        with engine.begin() as conn:
            # Step 1: Check if table exists
            print("Step 1: Checking if 'professor_lists' table exists...")
            table_exists = conn.execute(
                text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'professor_lists'
                    )
                """)
            ).scalar()
            
            if not table_exists:
                print("✗ 'professor_lists' table does not exist!")
                print("  Please run 'python setup_database.py' first.")
                return False
            print("✓ 'professor_lists' table exists")

            # Step 2: Check for duplicate user_email entries
            print("\nStep 2: Checking for duplicate user_email entries...")
            duplicates = conn.execute(
                text("""
                    SELECT user_email, COUNT(*) as count
                    FROM professor_lists
                    GROUP BY user_email
                    HAVING COUNT(*) > 1
                """)
            ).fetchall()
            
            if duplicates:
                print(f"⚠️  Found {len(duplicates)} user(s) with multiple entries:")
                for user_email, count in duplicates:
                    print(f"   - {user_email}: {count} entries")
                
                print("\n  Keeping the most recent entry for each user...")
                # Delete older entries, keep the most recent one
                for user_email, _ in duplicates:
                    conn.execute(
                        text("""
                            DELETE FROM professor_lists
                            WHERE id NOT IN (
                                SELECT id FROM professor_lists
                                WHERE user_email = :user_email
                                ORDER BY created_at DESC
                                LIMIT 1
                            )
                            AND user_email = :user_email
                        """),
                        {"user_email": user_email}
                    )
                print("✓ Duplicate entries removed")
            else:
                print("✓ No duplicate entries found")

            # Step 3: Check if unique constraint already exists
            print("\nStep 3: Checking for existing unique constraint...")
            constraint_exists = conn.execute(
                text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.table_constraints
                        WHERE table_name = 'professor_lists'
                        AND constraint_name = 'uq_professor_list_user'
                        AND constraint_type = 'UNIQUE'
                    )
                """)
            ).scalar()
            
            if constraint_exists:
                print("✓ Unique constraint 'uq_professor_list_user' already exists")
            else:
                # Add unique constraint
                print("  Adding unique constraint on user_email...")
                try:
                    conn.execute(
                        text("""
                            ALTER TABLE professor_lists
                            ADD CONSTRAINT uq_professor_list_user
                            UNIQUE (user_email)
                        """)
                    )
                    print("✓ Unique constraint added successfully")
                except SQLAlchemyError as e:
                    error_str = str(e)
                    if "already exists" in error_str.lower():
                        print("✓ Constraint already exists (different name)")
                    else:
                        raise

            # Step 4: Verify constraint
            print("\nStep 4: Verifying constraint...")
            constraint_check = conn.execute(
                text("""
                    SELECT constraint_name, constraint_type
                    FROM information_schema.table_constraints
                    WHERE table_name = 'professor_lists'
                    AND constraint_type = 'UNIQUE'
                """)
            ).fetchall()
            
            if constraint_check:
                print("✓ Unique constraint verified:")
                for name, ctype in constraint_check:
                    print(f"   - {name} ({ctype})")
            else:
                print("⚠️  No unique constraint found (may need manual intervention)")

        print("\n" + "=" * 60)
        print("✓ Migration completed successfully!")
        print("=" * 60)
        print("\nThe professor_lists table now enforces one row per user.")
        return True

    except SQLAlchemyError as exc:
        print(f"\n✗ Migration failed: {exc}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        engine.dispose()


if __name__ == "__main__":
    success = migrate_professor_lists()
    if not success:
        print("\n⚠️  Migration did not complete successfully.")
        sys.exit(1)
    else:
        print("\n✅ Database schema updated!")

