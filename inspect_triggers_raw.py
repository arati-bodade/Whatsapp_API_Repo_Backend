from db.session import SessionLocal
from sqlalchemy import text
import json

def inspect_db_raw():
    db = SessionLocal()
    try:
        # Check all triggers raw
        print("--- Google Sheet Triggers ---")
        result = db.execute(text("SELECT trigger_id, sheet_id, device_id, is_enabled, trigger_type, execution_time FROM google_sheet_triggers")).fetchall()
        for row in result:
            print(f"Trigger {row[0]}: Sheet={row[1]}, Device={row[2]}, Enabled={row[3]}, Type={row[4]}, Time={row[5]}")
            
        # Check all devices raw
        print("\n--- Active Devices ---")
        result = db.execute(text("SELECT device_id, device_name, session_status, is_active FROM devices WHERE is_active = true")).fetchall()
        for row in result:
            print(f"Device {row[0]}: Name={row[1]}, Status={row[2]}, Active={row[3]}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_db_raw()
