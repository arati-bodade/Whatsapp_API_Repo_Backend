#!/usr/bin/env python3
"""
Check device table names
"""
import psycopg2
from psycopg2.extras import RealDictCursor

def check_device_tables():
    db_url = 'postgresql://whatsapp_patform_user:cCR4XEVKwlV3XdoOmWbGw6rdNTyBOppm@dpg-d5fp9qlactks739q3o20-a.oregon-postgres.render.com/whatsapp_patform?sslmode=require'
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%device%'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        print('Device-related tables:')
        for table in tables:
            print(f'   {table["table_name"]}')
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    check_device_tables()
