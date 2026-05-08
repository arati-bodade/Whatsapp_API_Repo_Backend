#!/usr/bin/env python3

from sqlalchemy import create_engine, text
from db.base import engine

def check_trigger_enabled_column():
    """Check trigger_enabled column in google_sheets table"""
    
    try:
        with engine.connect() as conn:
            # Check trigger_enabled column details
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'google_sheets' 
                AND column_name = 'trigger_enabled'
            """))
            column_info = result.fetchone()
            
            if column_info:
                print(f'trigger_enabled column:')
                print(f'  name: {column_info[0]}')
                print(f'  type: {column_info[1]}')
                print(f'  nullable: {column_info[2]}')
                print(f'  default: {column_info[3]}')
            else:
                print('❌ trigger_enabled column not found!')
                
            # Check for NULL values
            result = conn.execute(text("""
                SELECT COUNT(*) as total_rows,
                       COUNT(trigger_enabled) as non_null_rows,
                       COUNT(*) - COUNT(trigger_enabled) as null_rows
                FROM google_sheets
            """))
            stats = result.fetchone()
            print(f'\nData statistics:')
            print(f'  total rows: {stats[0]}')
            print(f'  non-null rows: {stats[1]}')
            print(f'  null rows: {stats[2]}')
                
    except Exception as e:
        print(f"❌ Error checking column: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_trigger_enabled_column()
