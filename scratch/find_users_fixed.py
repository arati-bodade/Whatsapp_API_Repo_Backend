from sqlalchemy import create_engine, text
import os

# Using the URL from core/config.py
DATABASE_URL = "postgresql://whatsapp_platform_mhnw_user:nComdm17QkuwCzuxi2sMjZrIbXXLV8FG@dpg-d7cbd05ckfvc7387lfog-a.oregon-postgres.render.com/whatsapp_platform_mhnw"

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT email, username FROM master_admins LIMIT 5"))
        print("Admins:")
        for row in result:
            print(f"  {row.email} | {row.username}")
        
        result = conn.execute(text("SELECT email, username, role FROM resellers LIMIT 5"))
        print("\nResellers:")
        for row in result:
            print(f"  {row.email} | {row.username}")
except Exception as e:
    print(f"Error: {e}")
