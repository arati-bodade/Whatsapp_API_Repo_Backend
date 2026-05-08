#!/usr/bin/env python3
"""
Check current database schema for google_sheet_triggers
"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('DATABASE_URL')
engine = create_engine(db_url)

with engine.connect() as conn:
    result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'google_sheet_triggers'"))
    columns = [row.column_name for row in result]
    print('Current columns in google_sheet_triggers:')
    for col in sorted(columns):
        print(f'  - {col}')
    
    missing_cols = []
    required_cols = ['phone_column', 'status_column', 'trigger_value', 'last_processed_row']
    for col in required_cols:
        if col not in columns:
            missing_cols.append(col)
    
    if missing_cols:
        print(f'\n❌ Missing columns: {missing_cols}')
    else:
        print('\n✅ All required columns present')
