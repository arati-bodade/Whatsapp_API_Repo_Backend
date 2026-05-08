import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('DATABASE_URL')
engine = create_engine(db_url)

with engine.connect() as conn:
    # Check triggers table structure first
    result = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'google_sheet_triggers' ORDER BY ordinal_position"))
    columns = result.fetchall()
    print('Google Sheet Triggers table columns:')
    for col in columns:
        print(f'  {col[0]}: {col[1]}')
    
    print()
    
    # Check triggers table data
    result = conn.execute(text('SELECT COUNT(*) FROM google_sheet_triggers'))
    trigger_count = result.scalar()
    print(f'Google Sheet Triggers table count: {trigger_count}')
    
    if trigger_count > 0:
        # Get available columns for sample data
        available_columns = [col[0] for col in columns]
        select_cols = ', '.join(available_columns[:6])  # Select first 6 columns
        result = conn.execute(text(f'SELECT {select_cols} FROM google_sheet_triggers LIMIT 5'))
        triggers = result.fetchall()
        print('Sample triggers:')
        for trigger in triggers:
            print(f'  {trigger}')
