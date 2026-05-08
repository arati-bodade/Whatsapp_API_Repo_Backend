#!/usr/bin/env python3
"""
Check table schemas to understand data types
"""

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()
db_url = os.getenv('DATABASE_URL')
engine = create_engine(db_url)

with engine.connect() as conn:
    tables = ['devices', 'google_sheet_triggers', 'sheet_trigger_history', 'google_sheets', 'whatsapp_inbox']
    
    for table in tables:
        print(f"\n📋 Table: {table}")
        print("-" * 50)
        result = conn.execute(text(f"""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = '{table}' AND column_name LIKE '%device_id%'
            ORDER BY ordinal_position
        """))
        
        for row in result:
            print(f"  {row.column_name}: {row.data_type} (nullable: {row.is_nullable}, default: {row.column_default})")
