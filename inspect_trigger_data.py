from db.session import SessionLocal
from sqlalchemy import text

def inspect_trigger_data():
    db = SessionLocal()
    try:
        trigger_id = "1307b3d8-1361-495a-aff2-dbaa90288de1"
        print(f"--- Trigger Data for {trigger_id} ---")
        result = db.execute(text(f"SELECT trigger_id, sheet_id, device_id, is_enabled, trigger_type, send_time_column FROM google_sheet_triggers WHERE trigger_id = '{trigger_id}'")).fetchone()
        
        if result:
            print(f"Trigger ID: {result[0]}")
            print(f"Sheet ID: {result[1]}")
            print(f"Device ID: {result[2]}")
            print(f"Is Enabled: {result[3]}")
            print(f"Trigger Type: {result[4]}")
            print(f"Send Time Column: {result[5]}")
        else:
            print("Trigger not found.")
            
        print("\n--- All Triggers ---")
        result = db.execute(text("SELECT trigger_id, sheet_id, device_id, is_enabled, trigger_type FROM google_sheet_triggers")).fetchall()
        for row in result:
            print(f"TID: {row[0]}, Sheet: {row[1]}, Device: {row[2]}, Enabled: {row[3]}, Type: {row[4]}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_trigger_data()
