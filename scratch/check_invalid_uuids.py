
import os
import uuid
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def check_invalid_uuids():
    db_url = os.getenv("DATABASE_URL")
    if "?sslmode=require" not in db_url:
        db_url += "?sslmode=require"
    engine = create_engine(db_url)
    
    tables_cols = [
        ("master_admins", "admin_id"),
        ("resellers", "reseller_id"),
        ("businesses", "busi_user_id"),
        ("devices", "device_id"),
        ("campaigns", "campaign_id"),
        ("google_sheets", "sheet_id"),
        ("google_sheet_triggers", "trigger_id"),
        ("whatsapp_messages", "id")
    ]
    
    any_invalid = False
    
    with engine.connect() as conn:
        for table, col in tables_cols:
            print(f"Checking {table}.{col} for invalid UUIDs...")
            try:
                result = conn.execute(text(f"SELECT {col} FROM {table} WHERE {col} IS NOT NULL"))
                for row in result:
                    val = row[0]
                    if not val: continue
                    try:
                        uuid.UUID(str(val))
                    except ValueError:
                        print(f"❌ INVALID UUID in {table}.{col}: {val}")
                        any_invalid = True
            except Exception as e:
                print(f"Error checking {table}.{col}: {e}")
                
    if not any_invalid:
        print("\n✅ All ID columns contain valid UUID strings!")
    else:
        print("\n⚠️ Some columns contain invalid UUID strings. Manual cleanup required before migration.")

if __name__ == "__main__":
    check_invalid_uuids()
