import psycopg2
from urllib.parse import urlparse

# Use the DATABASE_URL from .env.example
DATABASE_URL = "postgresql://whatsapp_patform_user:cCR4XEVKwlV3XdoOmWbGw6rdNTyBOppm@dpg-d5fp9qlactks739q3o20-a.oregon-postgres.render.com/whatsapp_patform"

try:
    # Parse the connection string
    parsed = urlparse(DATABASE_URL)
    
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port,
        database=parsed.path[1:],  # Remove leading slash
        user=parsed.username,
        password=parsed.password
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
