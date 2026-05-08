#!/usr/bin/env python3
"""
Add missing last_processed_row column to google_sheet_triggers table
"""
import psycopg2

def add_missing_column():
    db_url = 'postgresql://whatsapp_platform_user:VJEL91wM45f51Va0NOUbmUxru1q44YWW@dpg-d64mqhnfte5s738bimug-a.oregon-postgres.render.com/whatsapp_platform?sslmode=require'
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        print("Adding last_processed_row to google_sheet_triggers table...")
        
        # Add the missing column
        cursor.execute("""
            ALTER TABLE google_sheet_triggers
            ADD COLUMN IF NOT EXISTS last_processed_row INTEGER DEFAULT 0
        """)
        
        conn.commit()
        
        # Verify the column was added
        cursor.execute("""
            SELECT column_name, data_type, column_default
            FROM information_schema.columns
            WHERE table_name = 'google_sheet_triggers'
            AND column_name = 'last_processed_row'
        """)
        
        result = cursor.fetchone()
        
        if result:
            print(f"✅ last_processed_row added successfully!")
            print(f"   Type: {result[1]}")
            print(f"   Default: {result[2]}")
        else:
            print("❌ Failed to add column")
        
        cursor.close()
        conn.close()
        
        return result is not None
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    add_missing_column()
