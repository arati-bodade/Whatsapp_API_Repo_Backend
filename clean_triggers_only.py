import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('DATABASE_URL')
engine = create_engine(db_url)

with engine.connect() as conn:
    # Check current triggers count
    result = conn.execute(text('SELECT COUNT(*) FROM google_sheet_triggers'))
    trigger_count = result.scalar()
    print(f'Current triggers count: {trigger_count}')
    
    if trigger_count > 0:
        # Delete all triggers
        result = conn.execute(text('DELETE FROM google_sheet_triggers'))
        print(f'Deleted {result.rowcount} triggers')
        conn.commit()
        
        # Verify
        result = conn.execute(text('SELECT COUNT(*) FROM google_sheet_triggers'))
        final_count = result.scalar()
        print(f'Final triggers count: {final_count}')
    else:
        print('No triggers to delete')
