import sys
import os

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from core.config import settings

# Database URL
DATABASE_URL = settings.DATABASE_URL

def add_columns():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        try:
            # List of columns to check/add
            columns = [
                ("message_template", "TEXT"),
                ("phone_column", "VARCHAR"),
                ("trigger_column", "VARCHAR"),
                ("trigger_value", "VARCHAR"),
                ("webhook_url", "VARCHAR"),
                ("trigger_config", "JSONB")
            ]
            
            for col_name, col_type in columns:
                try:
                    conn.execute(text(f"ALTER TABLE google_sheet_triggers ADD COLUMN IF NOT EXISTS {col_name} {col_type}"))
                    print(f"✅ Added column {col_name}")
                except Exception as e:
                    print(f"⚠️ Could not add column {col_name}: {e}")
            
            conn.commit()
            print("Migration completed successfully.")
        except Exception as e:
            print(f"❌ Error during migration: {e}")

if __name__ == "__main__":
    add_columns()
