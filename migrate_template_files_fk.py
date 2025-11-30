"""
Migration script to add foreign key relationship from template_files to files table.

This script:
1. Adds file_id column to template_files table
2. Creates File records for existing template_files entries
3. Links template_files to files via foreign key
4. Makes file_path nullable (since we now have file_id)

Run this script after updating the ORM models:
    python migrate_template_files_fk.py
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

# Load environment variables
load_dotenv("model/server_info.env")

# Database configuration
DB_NAME = os.getenv("DB_NAME", "applyche_global")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "applyche")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5434"))

DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def check_column_exists(engine, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table"""
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = :table_name 
                AND column_name = :column_name
            """),
            {"table_name": table_name, "column_name": column_name}
        )
        return result.scalar() is not None


def check_foreign_key_exists(engine, table_name: str, constraint_name: str) -> bool:
    """Check if a foreign key constraint exists"""
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE table_name = :table_name 
                AND constraint_name = :constraint_name
                AND constraint_type = 'FOREIGN KEY'
            """),
            {"table_name": table_name, "constraint_name": constraint_name}
        )
        return result.scalar() is not None


def migrate_template_files():
    """Migrate template_files table to use foreign key to files table"""
    print("=" * 60)
    print("Template Files Foreign Key Migration")
    print("=" * 60)
    print(f"\nConnecting to database: {DB_NAME}")
    print(f"  Host: {DB_HOST}:{DB_PORT}")
    print(f"  User: {DB_USER}\n")

    engine = create_engine(DATABASE_URL, future=True)
    
    try:
        with engine.begin() as conn:
            # Step 1: Check if files table exists
            print("Step 1: Checking if 'files' table exists...")
            files_exists = conn.execute(
                text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'files'
                    )
                """)
            ).scalar()
            
            if not files_exists:
                print("✗ 'files' table does not exist!")
                print("  Please run 'python setup_database.py' first to create all tables.")
                return False
            print("✓ 'files' table exists")

            # Step 2: Check if template_files table exists
            print("\nStep 2: Checking if 'template_files' table exists...")
            template_files_exists = conn.execute(
                text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'template_files'
                    )
                """)
            ).scalar()
            
            if not template_files_exists:
                print("✗ 'template_files' table does not exist!")
                print("  Please run 'python setup_database.py' first to create all tables.")
                return False
            print("✓ 'template_files' table exists")

            # Step 3: Add file_id column if it doesn't exist
            print("\nStep 3: Adding 'file_id' column to 'template_files'...")
            if check_column_exists(engine, "template_files", "file_id"):
                print("✓ 'file_id' column already exists")
            else:
                # First, make file_path nullable (if it isn't already)
                print("  Making 'file_path' nullable...")
                conn.execute(
                    text("ALTER TABLE template_files ALTER COLUMN file_path DROP NOT NULL")
                )
                
                # Add file_id column (nullable initially)
                print("  Adding 'file_id' column...")
                conn.execute(
                    text("""
                        ALTER TABLE template_files 
                        ADD COLUMN file_id INTEGER
                    """)
                )
                print("✓ 'file_id' column added")

            # Step 4: Backfill existing template_files with File records
            print("\nStep 4: Backfilling existing template_files with File records...")
            
            # Get all template_files that don't have a file_id yet
            orphaned_files = conn.execute(
                text("""
                    SELECT tf.id, tf.email_template_id, tf.file_path, et.user_email
                    FROM template_files tf
                    JOIN email_templates et ON tf.email_template_id = et.id
                    WHERE tf.file_id IS NULL 
                    AND tf.file_path IS NOT NULL
                """)
            ).fetchall()
            
            if orphaned_files:
                print(f"  Found {len(orphaned_files)} template_files without file_id")
                print("  Creating File records and linking them...")
                
                created_count = 0
                for tf_id, template_id, file_path, user_email in orphaned_files:
                    # Check if a File record already exists for this path and user
                    existing_file = conn.execute(
                        text("""
                            SELECT id FROM files 
                            WHERE file_path = :file_path 
                            AND (owner_email = :user_email OR owner_email IS NULL)
                            LIMIT 1
                        """),
                        {"file_path": file_path, "user_email": user_email}
                    ).scalar()
                    
                    if existing_file:
                        # Use existing File record
                        file_id = existing_file
                    else:
                        # Create new File record
                        result = conn.execute(
                            text("""
                                INSERT INTO files (owner_email, file_path, created_at)
                                VALUES (:owner_email, :file_path, NOW())
                                RETURNING id
                            """),
                            {"owner_email": user_email, "file_path": file_path}
                        )
                        file_id = result.scalar()
                    
                    # Link template_file to file
                    conn.execute(
                        text("""
                            UPDATE template_files 
                            SET file_id = :file_id 
                            WHERE id = :tf_id
                        """),
                        {"file_id": file_id, "tf_id": tf_id}
                    )
                    created_count += 1
                
                print(f"✓ Created/linked {created_count} File records")
            else:
                print("✓ No orphaned template_files found (all already have file_id)")

            # Step 5: Make file_id NOT NULL (now that we've backfilled)
            print("\nStep 5: Making 'file_id' NOT NULL...")
            conn.execute(
                text("""
                    ALTER TABLE template_files 
                    ALTER COLUMN file_id SET NOT NULL
                """)
            )
            print("✓ 'file_id' is now NOT NULL")

            # Step 6: Add foreign key constraint
            print("\nStep 6: Adding foreign key constraint...")
            fk_name = "fk_template_files_file_id"
            if check_foreign_key_exists(engine, "template_files", fk_name):
                print(f"✓ Foreign key '{fk_name}' already exists")
            else:
                conn.execute(
                    text(f"""
                        ALTER TABLE template_files
                        ADD CONSTRAINT {fk_name}
                        FOREIGN KEY (file_id) 
                        REFERENCES files(id) 
                        ON DELETE CASCADE
                    """)
                )
                print(f"✓ Foreign key '{fk_name}' added")

            # Step 7: Create index on file_id for better query performance
            print("\nStep 7: Creating index on 'file_id'...")
            index_name = "idx_template_files_file_id"
            index_exists = conn.execute(
                text("""
                    SELECT EXISTS (
                        SELECT FROM pg_indexes 
                        WHERE tablename = 'template_files' 
                        AND indexname = :index_name
                    )
                """),
                {"index_name": index_name}
            ).scalar()
            
            if index_exists:
                print(f"✓ Index '{index_name}' already exists")
            else:
                conn.execute(
                    text(f"CREATE INDEX {index_name} ON template_files(file_id)")
                )
                print(f"✓ Index '{index_name}' created")

        print("\n" + "=" * 60)
        print("✓ Migration completed successfully!")
        print("=" * 60)
        print("\nThe template_files table now has:")
        print("  - file_id column (foreign key to files.id)")
        print("  - Foreign key constraint with CASCADE delete")
        print("  - Index on file_id for performance")
        print("  - file_path is nullable (for backward compatibility)")
        return True

    except SQLAlchemyError as exc:
        print(f"\n✗ Migration failed: {exc}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        engine.dispose()


if __name__ == "__main__":
    success = migrate_template_files()
    if not success:
        print("\n⚠️  Migration did not complete successfully.")
        print("   Please review the errors above and try again.")
        sys.exit(1)
    else:
        print("\n✅ You can now use the updated ORM models!")
        print("   Restart your FastAPI server to use the new schema.")

