import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    cursor = conn.cursor()
    
    # Check column type for google_sheet_triggers.sheet_id
    cursor.execute("""
        SELECT column_name, data_type, udt_name 
        FROM information_schema.columns 
        WHERE table_name = 'google_sheet_triggers' 
        AND column_name = 'sheet_id'
    """)
    
    result = cursor.fetchone()
    print('Current google_sheet_triggers.sheet_id column info:')
    print(f'Column: {result[0]}, Data Type: {result[1]}, UDT Name: {result[2]}')
    
    # Also check if table exists and sample data
    cursor.execute("SELECT COUNT(*) FROM google_sheet_triggers")
    count = cursor.fetchone()[0]
    print(f'Total rows in google_sheet_triggers: {count}')
    
    if count > 0:
        cursor.execute("SELECT sheet_id FROM google_sheet_triggers LIMIT 3")
        samples = cursor.fetchall()
        print('Sample sheet_id values:')
        for sample in samples:
            print(f'  {sample[0]} (type: {type(sample[0])})')
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f'Database connection error: {e}')
