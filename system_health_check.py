from db.session import SessionLocal
from models.device import Device
from models.busi_user import BusiUser
from sqlalchemy import func

def check_system():
    db = SessionLocal()
    try:
        devices = db.query(Device).all()
        connected = [d for d in devices if str(d.session_status) == 'SessionStatus.connected' or str(d.session_status) == 'connected']
        
        print(f"Total Devices: {len(devices)}")
        print(f"Connected Devices: {len(connected)}")
        
        # Check for any 500 error indicators in the DB (not many, but we can check if there are many sessions with status='error')
        # Wait, Device status is Enum, not likely to be 'error' unless status is string
        
        # Any business users with missing critical data?
        invalid_users = db.query(BusiUser).filter(
            (BusiUser.email == None) | (BusiUser.email == '') | (BusiUser.phone == None)
        ).count()
        print(f"Users with missing email/phone: {invalid_users}")
        
    except Exception as e:
        print(f"Error checking system: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_system()
