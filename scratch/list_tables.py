from sqlalchemy import create_engine, inspect
import os

# Using the URL from core/config.py
DATABASE_URL = "postgresql://whatsapp_platform_mhnw_user:nComdm17QkuwCzuxi2sMjZrIbXXLV8FG@dpg-d7cbd05ckfvc7387lfog-a.oregon-postgres.render.com/whatsapp_platform_mhnw"

engine = create_engine(DATABASE_URL)
inspector = inspect(engine)

print("Tables in database:")
print(inspector.get_table_names())
