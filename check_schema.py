#!/usr/bin/env python3

from sqlalchemy import create_engine, text
from db.base import engine

def check_google_sheets_schema():
    """Check the current schema of google_sheets table"""
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'google_sheets' 
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            
            print('Current google_sheets table schema:')
            for col in columns:
                print(f'  {col[0]}: {col[1]}')
                
            # Check if table exists at all
            table_check = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'google_sheets'
                );
            """))
            table_exists = table_check.scalar()
            
            if not table_exists:
                print("❌ google_sheets table does not exist!")
            else:
                print("✅ google_sheets table exists")
                
    except Exception as e:
        print(f"❌ Error checking schema: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_google_sheets_schema()
