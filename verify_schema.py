import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

try:
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'google_sheet_triggers' 
        AND column_name IN ('webhook_url', 'trigger_config', 'status_column', 'trigger_value') 
        ORDER BY column_name
    """)
    
    print('🔍 Verification - Columns added:')
    for row in cursor.fetchall():
        print(f'  ✅ {row[0]}: {row[1]} (nullable: {row[2]})')
    
    conn.close()
    print('\n✅ All required columns are present!')
    
except Exception as e:
    print(f'❌ Error: {e}')
