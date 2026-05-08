#!/usr/bin/env python3

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Get database connection"""
    # Try to get database URL from environment or use default
    db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/whatsapp_platform')
    
    # Parse the URL if needed (simplified)
    if db_url.startswith('postgresql://'):
        db_url = db_url.replace('postgresql://', 'postgresql://')
    
    return psycopg2.connect(db_url)

def create_google_sheets_tables():
    """Create Google Sheets tables using raw SQL"""
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("Creating google_sheets table...")
        
        # Create google_sheets table
        create_google_sheets_sql = """
        CREATE TABLE IF NOT EXISTS google_sheets (
            id VARCHAR PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES businesses(busi_user_id),
            sheet_name VARCHAR NOT NULL,
            spreadsheet_id VARCHAR NOT NULL,
            worksheet_name VARCHAR DEFAULT 'Sheet1',
            connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR DEFAULT 'ACTIVE',
            total_rows INTEGER DEFAULT 0,
            trigger_enabled BOOLEAN DEFAULT FALSE,
            device_id VARCHAR REFERENCES devices(device_id),
            message_template TEXT,
            trigger_config JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        cursor.execute(create_google_sheets_sql)
        print("✅ google_sheets table created")
        
        # Create sheet_trigger_history table
        print("Creating sheet_trigger_history table...")
        
        create_trigger_history_sql = """
        CREATE TABLE IF NOT EXISTS sheet_trigger_history (
            id VARCHAR PRIMARY KEY,
            sheet_id VARCHAR NOT NULL REFERENCES google_sheets(id),
            device_id VARCHAR,
            phone_number VARCHAR NOT NULL,
            message_content TEXT,
            status VARCHAR DEFAULT 'SENT',
            error_message TEXT,
            triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            row_data JSONB
        );
        """
        
        cursor.execute(create_trigger_history_sql)
        print("✅ sheet_trigger_history table created")
        
        # Create indexes for better performance
        print("Creating indexes...")
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_google_sheets_user_id ON google_sheets(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_google_sheets_spreadsheet_id ON google_sheets(spreadsheet_id);",
            "CREATE INDEX IF NOT EXISTS idx_sheet_trigger_history_sheet_id ON sheet_trigger_history(sheet_id);",
            "CREATE INDEX IF NOT EXISTS idx_sheet_trigger_history_triggered_at ON sheet_trigger_history(triggered_at);"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        print("✅ Indexes created")
        
        # Commit the transaction
        conn.commit()
        
        # Verify tables were created
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('google_sheets', 'sheet_trigger_history')
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print(f"\n✅ Created tables: {[table[0] for table in tables]}")
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    create_google_sheets_tables()
