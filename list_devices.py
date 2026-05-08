from db.session import SessionLocal
from models.device import Device
from models.busi_user import BusiUser
import json

def list_active_devices():
    db = SessionLocal()
    try:
        # Get first user to use as fallback ID if needed
        user = db.query(BusiUser).first()
        if not user:
            print("No users found in database.")
            return

        devices = db.query(Device).all()
        result = []
        for d in devices:
            result.append({
                "device_id": str(d.device_id),
                "name": d.device_name,
                "session_status": d.session_status,
                "user_id": str(d.busi_user_id)
            })
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    list_active_devices()
