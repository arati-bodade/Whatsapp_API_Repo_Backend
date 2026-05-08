#!/usr/bin/env python3
"""
Add missing status_column to google_sheet_triggers table
"""
import psycopg2

def add_missing_column():
    db_url = 'postgresql://whatsapp_platform_user:VJEL91wM45f51Va0NOUbmUxru1q44YWW@dpg-d64mqhnfte5s738bimug-a.oregon-postgres.render.com/whatsapp_platform?sslmode=require'
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        print("Adding status_column to google_sheet_triggers table...")
        
        # Add the missing column
        cursor.execute("""
            ALTER TABLE google_sheet_triggers
            ADD COLUMN status_column VARCHAR(255)
        """)
        
        # Backfill existing rows with default value
        cursor.execute("""
            UPDATE google_sheet_triggers
            SET status_column = 'Status'
            WHERE status_column IS NULL
        """)
        
        conn.commit()
        
        print("✅ status_column added successfully!")
        print("✅ Existing rows backfilled with 'Status'")
        
        # Verify the column was added
        cursor.execute("""
            SELECT COUNT(*) as total_rows,
                   COUNT(status_column) as rows_with_status
            FROM google_sheet_triggers
        """)
        
        result = cursor.fetchone()
        print(f"Total rows: {result[0]}")
        print(f"Rows with status_column: {result[1]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    add_missing_column()
