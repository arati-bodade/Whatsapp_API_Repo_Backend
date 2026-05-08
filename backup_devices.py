from db.session import SessionLocal
from models.device import Device
import json
from datetime import datetime

def backup_devices():
    db = SessionLocal()
    try:
        devices = db.query(Device).all()
        result = []
        for d in devices:
            # Convert to dict, handle non-serializable objects
            device_dict = {
                "device_id": str(d.device_id),
                "busi_user_id": str(d.busi_user_id),
                "device_name": d.device_name,
                "device_type": d.device_type.value if hasattr(d.device_type, 'value') else d.device_type,
                "session_status": d.session_status.value if hasattr(d.session_status, 'value') else d.session_status,
                "is_active": d.is_active,
                "created_at": d.created_at.isoformat() if d.created_at else None
            }
            result.append(device_dict)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"devices_backup_{timestamp}.json"
        with open(filename, "w") as f:
            json.dump(result, f, indent=2)
        print(f"Backup created: {filename} ({len(result)} devices)")
        return filename
    except Exception as e:
        print(f"Backup failed: {e}")
        return None
    finally:
        db.close()

if __name__ == "__main__":
    backup_devices()
