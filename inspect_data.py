from db.session import SessionLocal
import models # This imports everything in models/__init__.py
import json

def inspect_data():
    db = SessionLocal()
    try:
        from models.google_sheet import GoogleSheet, GoogleSheetTrigger
        from models.device import Device
        
        # Check all triggers
        triggers = db.query(GoogleSheetTrigger).all()
        print(f"Total triggers: {len(triggers)}")
        
        for t in triggers:
            print(f"Trigger ID: {t.trigger_id}")
            print(f"  Sheet ID: {t.sheet_id}")
            print(f"  Device ID: {t.device_id}")
            print(f"  Enabled: {t.is_enabled}")
            print(f"  Trigger Type: {t.trigger_type}")
            print(f"  Time column: {t.send_time_column}")
            print("-" * 20)
            
        # Check all devices
        devices = db.query(Device).filter(Device.is_active == True).all()
        print(f"\nActive Devices:")
        for d in devices:
            print(f"Device ID: {d.device_id}")
            print(f"  Name: {d.device_name}")
            print(f"  Status: {d.session_status}")
            print("-" * 20)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_data()
