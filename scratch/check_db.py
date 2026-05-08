import os
from sqlalchemy import create_engine, text

# Manually set for testing
db_url = "postgresql://neondb_owner:npg_I4dGpkvPi2zw@ep-snowy-mountain-an3w18e6-pooler.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
print(f"Testing connection to: {db_url}")

try:
    engine = create_engine(db_url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT current_database();"))
        db_name = result.scalar()
        print(f"SUCCESS: Connected to database: {db_name}")
        
        # List tables
        result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public';"))
        tables = [row[0] for row in result]
        print(f"Tables found ({len(tables)}):")
        for table in tables:
            print(f" - {table}")
            
        if len(tables) == 0:
            print("WARNING: No tables found in the public schema. Database might be empty.")
        else:
            print("SUCCESS: Database schema seems initialized.")

except Exception as e:
    print(f"ERROR: Connection failed: {e}")
