from sqlalchemy import create_engine, inspect
import os

# Using the URL from core/config.py
DATABASE_URL = "postgresql://whatsapp_platform_mhnw_user:nComdm17QkuwCzuxi2sMjZrIbXXLV8FG@dpg-d7cbd05ckfvc7387lfog-a.oregon-postgres.render.com/whatsapp_platform_mhnw"

engine = create_engine(DATABASE_URL)
inspector = inspect(engine)

tables = ["businesses", "resellers", "master_admins", "devices", "plans", "campaigns"]

for table in tables:
    print(f"\nTable: {table}")
    try:
        columns = inspector.get_columns(table)
        for column in columns:
            if "id" in column['name'].lower():
                print(f"  {column['name']}: {column['type']}")
    except Exception as e:
        print(f"  Error inspecting table: {e}")
