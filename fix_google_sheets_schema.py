"""Manual migration script for Google Sheets trigger schema fix
Run this with: python fix_google_sheets_schema.py
"""

import os
import psycopg2
from dotenv import load_dotenv

def main():
    load_dotenv()
    
    # Database connection
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("ERROR: DATABASE_URL not found in environment")
        return
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        print("🔧 Starting Google Sheets schema migration...")
        
        # Add webhook_url column
        cursor.execute("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'google_sheet_triggers' 
                    AND column_name = 'webhook_url'
                ) THEN
                    ALTER TABLE google_sheet_triggers 
                    ADD COLUMN webhook_url VARCHAR(255);
                    RAISE NOTICE 'Added webhook_url column';
                END IF;
            END $$;
        """)
        
        # Add trigger_config column
        cursor.execute("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'google_sheet_triggers' 
                    AND column_name = 'trigger_config'
                ) THEN
                    ALTER TABLE google_sheet_triggers 
                    ADD COLUMN trigger_config JSONB;
                    RAISE NOTICE 'Added trigger_config column';
                END IF;
            END $$;
        """)
        
        # Add status_column column with default
        cursor.execute("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'google_sheet_triggers' 
                    AND column_name = 'status_column'
                ) THEN
                    ALTER TABLE google_sheet_triggers 
                    ADD COLUMN status_column VARCHAR(100) DEFAULT 'Status';
                    
                    UPDATE google_sheet_triggers 
                    SET status_column = 'Status' 
                    WHERE status_column IS NULL;
                    
                    RAISE NOTICE 'Added status_column column with default';
                END IF;
            END $$;
        """)
        
        # Add trigger_value column with default
        cursor.execute("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'google_sheet_triggers' 
                    AND column_name = 'trigger_value'
                ) THEN
                    ALTER TABLE google_sheet_triggers 
                    ADD COLUMN trigger_value VARCHAR(100) DEFAULT 'Send';
                    
                    UPDATE google_sheet_triggers 
                    SET trigger_value = 'Send' 
                    WHERE trigger_value IS NULL;
                    
                    RAISE NOTICE 'Added trigger_value column with default';
                END IF;
            END $$;
        """)
        
        conn.commit()
        
        # Verify the changes
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'google_sheet_triggers' 
            AND column_name IN ('webhook_url', 'trigger_config', 'status_column', 'trigger_value')
            ORDER BY column_name
        """)
        
        columns = cursor.fetchall()
        
        print("\n✅ Migration completed successfully!")
        print("\n📋 Added columns:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]} (nullable: {col[2]})")
        
        print("\n🎯 Your FastAPI app should now start without UndefinedColumn errors!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
