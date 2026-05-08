import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        database=os.getenv('DB_NAME', 'whatsapp'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'postgres')
    )
    cursor = conn.cursor()
    
    # Check enum values
    cursor.execute("SELECT unnest(enum_range(NULL::devicetype));")
    enum_values = cursor.fetchall()
    
    print('PostgreSQL devicetype enum values:')
    for value in enum_values:
        print(f'  - {value[0]}')
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f'Error: {e}')
