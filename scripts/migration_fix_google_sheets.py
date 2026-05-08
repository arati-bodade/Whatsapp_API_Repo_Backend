import sys
import os
import sqlalchemy
from sqlalchemy import create_engine, text

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db.base import engine

def migrate_google_sheets():
    print("Starting migration for google_sheets table...")
    
    commands = [
        # 1. Rename columns if they exist
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
        
        # 2. Add missing columns safely
        "ALTER TABLE google_sheets ADD COLUMN IF NOT EXISTS worksheet_name VARCHAR DEFAULT 'Sheet1';",
        "ALTER TABLE google_sheets ADD COLUMN IF NOT EXISTS trigger_enabled BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE google_sheets ADD COLUMN IF NOT EXISTS device_id VARCHAR NULL;",
        "ALTER TABLE google_sheets ADD COLUMN IF NOT EXISTS message_template TEXT NULL;",
        "ALTER TABLE google_sheets ADD COLUMN IF NOT EXISTS trigger_config JSON DEFAULT NULL;",
        "ALTER TABLE google_sheets ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();",
        "ALTER TABLE google_sheets ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();",
        
        # 3. Ensure Primary Key
        # If 'id' is not PK, make it PK (requires it to be unique and not null)
        # We assume it is unique if it was 'sheet_id'
        # "ALTER TABLE google_sheets ADD PRIMARY KEY (id);" -> Might fail if constraint exists with different name
        
        # 4. Sheet Trigger History fixes?
        # Ensure sheet_trigger_history.sheet_id references google_sheets.id
    ]

    try:
        with engine.connect() as conn:
            for cmd in commands:
                print(f"Executing: {cmd[:50]}...")
                conn.execute(text(cmd))
                conn.commit()
            print("Migration completed successfully.")
            
    except Exception as e:
        print(f"Migration Failed: {e}")

if __name__ == "__main__":
    migrate_google_sheets()
