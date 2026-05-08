from sqlalchemy import create_engine, inspect
import os

# Using the URL from core/config.py
DATABASE_URL = "postgresql://whatsapp_platform_mhnw_user:nComdm17QkuwCzuxi2sMjZrIbXXLV8FG@dpg-d7cbd05ckfvc7387lfog-a.oregon-postgres.render.com/whatsapp_platform_mhnw"

engine = create_engine(DATABASE_URL)
inspector = inspect(engine)

for table in inspector.get_table_names():
    # print(f"\nTable: {table}")
    columns = inspector.get_columns(table)
    for column in columns:
        if str(column['type']).upper() == 'UUID':
            print(f"CRITICAL: Found UUID column in {table}.{column['name']}")
        if "id" in column['name'].lower() and "VARCHAR" not in str(column['type']).upper() and "INTEGER" not in str(column['type']).upper():
             print(f"POTENTIAL MISMATCH: {table}.{column['name']} has type {column['type']}")
