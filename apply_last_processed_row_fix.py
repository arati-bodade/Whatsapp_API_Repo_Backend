#!/usr/bin/env python3
"""
Direct SQL fix for missing last_processed_row column
"""
import psycopg2
from psycopg2.extras import RealDictCursor

def apply_fix():
    db_url = 'postgresql://whatsapp_patform_user:cCR4XEVKwlV3XdoOmWbGw6rdNTyBOppm@dpg-d5fp9qlactks739q3o20-a.oregon-postgres.render.com/whatsapp_patform?sslmode=require'
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        print("🔧 APPLYING DIRECT SQL FIX FOR last_processed_row")
        
        # Add the column
        cursor.execute('''
            ALTER TABLE google_sheet_triggers 
            ADD COLUMN IF NOT EXISTS last_processed_row INTEGER DEFAULT 0
        ''')
        
        # Update existing rows
        cursor.execute('''
            UPDATE google_sheet_triggers 
            SET last_processed_row = 0 
            WHERE last_processed_row IS NULL
        ''')
        
        # Make it NOT NULL
        cursor.execute('''
            ALTER TABLE google_sheet_triggers 
            ALTER COLUMN last_processed_row SET NOT NULL
        ''')
        
        conn.commit()
        
        print("✅ last_processed_row column added successfully")
        
        # Verify the fix
        cursor.execute('''
            SELECT column_name, data_type, column_default, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'google_sheet_triggers'
            AND column_name = 'last_processed_row'
        ''')
        
        result = cursor.fetchone()
        
        if result:
            print(f"✅ VERIFICATION:")
            print(f"   Column: {result[0]}")
            print(f"   Type: {result[1]}")
            print(f"   Default: {result[2]}")
            print(f"   Nullable: {result[3]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f'❌ SQL fix error: {e}')
        return False

if __name__ == "__main__":
    apply_fix()
