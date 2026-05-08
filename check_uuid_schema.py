#!/usr/bin/env python3

from sqlalchemy import create_engine, text
from db.base import engine

def check_uuid_schema():
    """Check UUID column types in database"""
    
    try:
        with engine.connect() as conn:
            # Check sheet_trigger_history schema
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'sheet_trigger_history' 
                AND column_name = 'device_id'
            """))
            sheet_hist = result.fetchone()
            print(f'sheet_trigger_history.device_id: {sheet_hist[0]} = {sheet_hist[1]}')
            
            # Check devices schema
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'devices' 
                AND column_name = 'device_id'
            """))
            device = result.fetchone()
            print(f'devices.device_id: {device[0]} = {device[1]}')
            
    except Exception as e:
        print(f"❌ Error checking schema: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_uuid_schema()
