from db.session import SessionLocal
from models.device import Device
import uuid

db = SessionLocal()
device_id = "39582353-642d-4447-8164-f24f94f54bc7"
try:
    # Try exact match
    device = db.query(Device).filter(Device.device_id == uuid.UUID(device_id)).first()
    if device:
        print(f"Device {device_id} found! Name: {device.device_name}, Status: {device.session_status}")
    else:
        print(f"Device {device_id} NOT FOUND in database.")
    
    # Try all devices to see if anything else is there
    print("\nAll devices in DB:")
    all_devices = db.query(Device).all()
    for d in all_devices:
        print(f"- {d.device_id} ({d.device_name}) [Status: {d.session_status}]")
        
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
