import sys
import os
from sqlalchemy import create_engine, text

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db.base import engine

def migrate_google_sheets_v2():
    print("Starting ROBUST migration for google_sheets table...")
    
    commands = [
        # 1. Rename columns if still needed (idempotent checks)
        """
        DO $$
        BEGIN
            IF EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name='google_sheets' AND column_name='sheet_id') THEN
                ALTER TABLE google_sheets RENAME COLUMN sheet_id TO id;
            END IF;
            
            IF EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name='google_sheets' AND column_name='rows_count') THEN
                ALTER TABLE google_sheets RENAME COLUMN rows_count TO total_rows;
            END IF;
        END $$;
        """,
        
        # 2. Add ALL potential missing columns
        "ALTER TABLE google_sheets ADD COLUMN IF NOT EXISTS total_rows INTEGER DEFAULT 0;", # This was the specific crash cause
        "ALTER TABLE google_sheets ADD COLUMN IF NOT EXISTS worksheet_name VARCHAR DEFAULT 'Sheet1';",
        "ALTER TABLE google_sheets ADD COLUMN IF NOT EXISTS trigger_enabled BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE google_sheets ADD COLUMN IF NOT EXISTS device_id VARCHAR NULL;",
        "ALTER TABLE google_sheets ADD COLUMN IF NOT EXISTS message_template TEXT NULL;",
        "ALTER TABLE google_sheets ADD COLUMN IF NOT EXISTS trigger_config JSON DEFAULT NULL;",
        "ALTER TABLE google_sheets ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();",
        "ALTER TABLE google_sheets ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();",
        
        # 3. Fix user_id type (ensure it is VARCHAR for FK)
        # We drop the constraint first to be safe, then alter, then re-add
        "ALTER TABLE google_sheets DROP CONSTRAINT IF EXISTS google_sheets_user_id_fkey;",
        "ALTER TABLE google_sheets ALTER COLUMN user_id TYPE VARCHAR(50) USING user_id::text;",
        """
        ALTER TABLE google_sheets 
        ADD CONSTRAINT google_sheets_user_id_fkey 
        FOREIGN KEY (user_id) REFERENCES businesses(busi_user_id);
        """
    ]

    try:
        with engine.connect() as conn:
            for cmd in commands:
                print(f"Executing: {cmd[:60]}...")
                conn.execute(text(cmd))
                conn.commit()
            print("Migration V2 completed successfully.")
            
    except Exception as e:
        print(f"Migration V2 Failed: {e}")

if __name__ == "__main__":
    migrate_google_sheets_v2()
