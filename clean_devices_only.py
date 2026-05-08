import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('DATABASE_URL')
engine = create_engine(db_url)

with engine.connect() as conn:
    # Check current devices count
    result = conn.execute(text('SELECT COUNT(*) FROM devices'))
    device_count = result.scalar()
    print(f'Current devices count: {device_count}')
    
    if device_count > 0:
        # Delete all devices
        result = conn.execute(text('DELETE FROM devices'))
        print(f'Deleted {result.rowcount} devices')
        conn.commit()
        
        # Verify
        result = conn.execute(text('SELECT COUNT(*) FROM devices'))
        final_count = result.scalar()
        print(f'Final devices count: {final_count}')
    else:
        print('No devices to delete')
