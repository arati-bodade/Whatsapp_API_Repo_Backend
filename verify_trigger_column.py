#!/usr/bin/env python3
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('DATABASE_URL')
engine = create_engine(db_url)

with engine.connect() as conn:
    result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'google_sheet_triggers' AND column_name = 'trigger_column'"))
    if result.fetchone():
        print('✅ trigger_column exists in google_sheet_triggers')
    else:
        print('❌ trigger_column still missing')
