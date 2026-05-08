import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL not found")
    exit(1)

# Ensure sslmode=require if it's a Render DB
if "render.com" in DATABASE_URL and "sslmode" not in DATABASE_URL:
    DATABASE_URL += "?sslmode=require"

engine = create_engine(DATABASE_URL)

def migrate():
    with engine.connect() as conn:
        targets = [
            ("businesses", "busi_user_id"),
            ("businesses", "created_by"),
            ("devices", "device_id"),
            ("devices", "busi_user_id"),
            ("google_sheets", "id"),
            ("google_sheets", "user_id"),
            ("google_sheets", "device_id"),
            ("google_sheet_triggers", "trigger_id"),
            ("google_sheet_triggers", "user_id"),
            ("google_sheet_triggers", "sheet_id"),
            ("google_sheet_triggers", "device_id"),
            ("sheet_trigger_history", "id"),
            ("sheet_trigger_history", "sheet_id"),
            ("sheet_trigger_history", "trigger_id"),
            ("sheet_trigger_history", "device_id"),
        ]
        
        for table, col in targets:
            print(f"Migrating {table}.{col}...")
            try:
                # Check current type
                sql_check = text(f"SELECT data_type FROM information_schema.columns WHERE table_name = '{table}' AND column_name = '{col}'")
                res = conn.execute(sql_check).scalar()
                if res == 'uuid':
                    print(f"  Already UUID. Skip.")
                    continue
                
                # Convert
                sql_alter = text(f"ALTER TABLE {table} ALTER COLUMN {col} TYPE UUID USING {col}::uuid")
                conn.execute(sql_alter)
                conn.commit()
                print(f"  Successfully converted.")
            except Exception as e:
                print(f"  Error migrating {table}.{col}: {e}")
                conn.rollback()

if __name__ == "__main__":
    migrate()
