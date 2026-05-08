from db.session import SessionLocal
from models import Device, GoogleSheetTrigger
import json
from uuid import UUID

def inspect_trigger_and_devices():
    db = SessionLocal()
    try:
        # Check all triggers
        triggers = db.query(GoogleSheetTrigger).all()
        print(f"Total triggers: {len(triggers)}")
        
        for t in triggers:
            print(f"Trigger ID: {t.trigger_id}")
            print(f"  Sheet ID: {t.sheet_id}")
            print(f"  Device ID: {t.device_id}")
            print(f"  Enabled: {t.is_enabled}")
            print(f"  Trigger Typ: {t.trigger_type}")
            print(f"  Execution Time: {t.execution_time}")
            print("-" * 20)
            
        # Check all devices
        devices = db.query(Device).filter(Device.is_active == True).all()
        print(f"\nActive Devices:")
        for d in devices:
            print(f"Device ID: {d.device_id}")
            print(f"  Name: {d.device_name}")
            print(f"  Status: {d.session_status}")
            print("-" * 20)
            
    finally:
        db.close()

if __name__ == "__main__":
    inspect_trigger_and_devices()
