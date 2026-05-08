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
    
    # Check if 'official' exists in the enum
    cursor.execute("SELECT unnest(enum_range(NULL::devicetype));")
    enum_values = cursor.fetchall()
    
    print('Current PostgreSQL devicetype enum values:')
    for value in enum_values:
        print(f'  - {value[0]}')
    
    # Check if official exists
    has_official = any(value[0] == 'official' for value in enum_values)
    print(f'\nHas "official" in enum: {has_official}')
    
    if not has_official:
        print('\nNeed to add "official" to the enum...')
        cursor.execute("ALTER TYPE devicetype ADD VALUE 'official';")
        conn.commit()
        print('✅ Added "official" to devicetype enum')
        
        # Verify
        cursor.execute("SELECT unnest(enum_range(NULL::devicetype));")
        enum_values = cursor.fetchall()
        print('\nUpdated PostgreSQL devicetype enum values:')
        for value in enum_values:
            print(f'  - {value[0]}')
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f'Error: {e}')
