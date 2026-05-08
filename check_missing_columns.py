#!/usr/bin/env python3
"""
Check database schema for google_sheet_triggers - missing columns
"""
import psycopg2
from psycopg2.extras import RealDictCursor

def check_missing_columns():
    db_url = 'postgresql://whatsapp_patform_user:cCR4XEVKwlV3XdoOmWbGw6rdNTyBOppm@dpg-d5fp9qlactks739q3o20-a.oregon-postgres.render.com/whatsapp_patform?sslmode=require'
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check all columns in the table
        cursor.execute("""
            SELECT column_name, data_type, column_default
            FROM information_schema.columns
            WHERE table_name = 'google_sheet_triggers'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        print(f'Current columns ({len(columns)}):')
        for col in columns:
            print(f'   {col["column_name"]}: {col["data_type"]}')
        
        # Check for missing columns
        existing_columns = [col['column_name'] for col in columns]
        missing_columns = []
        
        if 'status_column' not in existing_columns:
            missing_columns.append('status_column')
        if 'trigger_column' not in existing_columns:
            missing_columns.append('trigger_column')
            
        if missing_columns:
            print(f'\nMissing columns: {missing_columns}')
        else:
            print('\n✅ All required columns exist')
        
        cursor.close()
        conn.close()
        
        return missing_columns
        
    except Exception as e:
        print(f'Database error: {e}')
        return []

if __name__ == "__main__":
    check_missing_columns()
