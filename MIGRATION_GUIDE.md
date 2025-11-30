# Migration Guide: Adding Foreign Key to template_files

This guide explains how to update your database schema to add the foreign key relationship from `template_files` to `files` table.

## Overview

We've updated the ORM models to add a `file_id` foreign key column to the `template_files` table. This allows:
- Each email template to reference multiple files via the `files` table
- Better data integrity with foreign key constraints
- Easier file management and reuse

## Migration Options

### Option 1: Full Migration Script (Recommended)

Use this if you have existing data in `template_files` table:

```bash
python migrate_template_files_fk.py
```

**What it does:**
1. ✅ Adds `file_id` column to `template_files`
2. ✅ Creates `File` records for existing `template_files` entries
3. ✅ Links existing `template_files` to new `File` records
4. ✅ Adds foreign key constraint
5. ✅ Creates index for performance
6. ✅ Makes `file_path` nullable (for backward compatibility)

**When to use:** Production databases with existing data

---

### Option 2: ORM Schema Update (Simple)

Use this if you're starting fresh or don't have existing data:

```bash
python update_schema_with_orm.py
```

**What it does:**
1. ✅ Creates new tables if they don't exist
2. ✅ Adds new columns if they don't exist
3. ⚠️ Does NOT backfill existing data
4. ⚠️ Does NOT modify existing columns

**When to use:** Development, fresh databases, or after running Option 1

---

## Step-by-Step Instructions

### For Existing Databases (Production)

1. **Backup your database** (recommended):
   ```bash
   pg_dump -h localhost -p 5434 -U postgres applyche_global > backup_before_migration.sql
   ```

2. **Run the migration script**:
   ```bash
   python migrate_template_files_fk.py
   ```

3. **Verify the migration**:
   ```sql
   -- Check that file_id column exists
   SELECT column_name, data_type, is_nullable 
   FROM information_schema.columns 
   WHERE table_name = 'template_files' AND column_name = 'file_id';
   
   -- Check foreign key constraint
   SELECT constraint_name, constraint_type 
   FROM information_schema.table_constraints 
   WHERE table_name = 'template_files' AND constraint_type = 'FOREIGN KEY';
   
   -- Verify data was migrated
   SELECT COUNT(*) FROM template_files WHERE file_id IS NOT NULL;
   ```

4. **Restart your FastAPI server**:
   ```bash
   python -m uvicorn api.main:app --reload
   ```

### For Fresh Databases (Development)

1. **Run setup script** (if not done already):
   ```bash
   python setup_database.py
   ```

2. **Run ORM schema update**:
   ```bash
   python update_schema_with_orm.py
   ```

3. **Seed test data** (optional):
   ```bash
   python seed_test_data.py
   ```

4. **Start FastAPI server**:
   ```bash
   python -m uvicorn api.main:app --reload
   ```

---

## What Changed in the Schema

### Before:
```sql
template_files:
  - id (PK)
  - email_template_id (FK to email_templates)
  - file_path (TEXT, NOT NULL)  -- Just a string path
```

### After:
```sql
template_files:
  - id (PK)
  - email_template_id (FK to email_templates)
  - file_id (FK to files.id, NOT NULL)  -- NEW: Foreign key
  - file_path (TEXT, NULLABLE)  -- Now nullable, kept for compatibility

files:
  - id (PK)
  - owner_email (FK to users)
  - file_path (TEXT, NOT NULL)
  - created_at (TIMESTAMP)
```

---

## Troubleshooting

### Error: "column file_id does not exist"
- **Solution:** Run `migrate_template_files_fk.py` first

### Error: "foreign key constraint violation"
- **Solution:** The migration script should handle this, but if it fails:
  1. Check that `files` table exists
  2. Verify existing `template_files` have valid `file_path` values
  3. Run the migration script again

### Error: "relation 'template_files' does not exist"
- **Solution:** Run `python setup_database.py` first to create all tables

### Existing template_files have NULL file_path
- **Solution:** The migration script will skip these. You may need to manually:
  1. Create `File` records for missing paths
  2. Update `template_files` to link to those `File` records

---

## Verification Queries

After migration, run these to verify everything worked:

```sql
-- 1. Check column exists
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'template_files' 
ORDER BY ordinal_position;

-- 2. Check foreign key
SELECT 
    tc.constraint_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name 
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.table_name = 'template_files' 
  AND tc.constraint_type = 'FOREIGN KEY';

-- 3. Check data integrity
SELECT 
    COUNT(*) as total_template_files,
    COUNT(file_id) as files_with_fk,
    COUNT(*) - COUNT(file_id) as missing_fk
FROM template_files;

-- 4. Sample data
SELECT 
    tf.id,
    tf.email_template_id,
    tf.file_id,
    f.file_path,
    f.owner_email
FROM template_files tf
LEFT JOIN files f ON tf.file_id = f.id
LIMIT 10;
```

---

## Rollback (If Needed)

If you need to rollback the migration:

```sql
-- Remove foreign key constraint
ALTER TABLE template_files DROP CONSTRAINT IF EXISTS fk_template_files_file_id;

-- Remove index
DROP INDEX IF EXISTS idx_template_files_file_id;

-- Remove column (WARNING: This will lose data!)
-- ALTER TABLE template_files DROP COLUMN IF EXISTS file_id;

-- Make file_path NOT NULL again
ALTER TABLE template_files ALTER COLUMN file_path SET NOT NULL;
```

**Note:** Only rollback if absolutely necessary. The migration is designed to be safe and preserve all existing data.

---

## Next Steps

After successful migration:

1. ✅ Restart FastAPI server
2. ✅ Test creating/updating email templates via API
3. ✅ Verify file attachments work correctly
4. ✅ Check that existing templates still load properly

The API now supports both:
- `file_paths` parameter (creates new File records)
- `file_ids` parameter (reuses existing File records)

See `api/routes/email_templates.py` for details.

