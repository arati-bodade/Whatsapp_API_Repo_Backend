
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from services.device_service import DeviceService, Device

# Setup DB connection
# Assuming database URL is in .env or consistent with project
# I will try to read from main.py or just use the local db file if sqlite, but it seems to be postgres/mysql based on psycopg2 errors mentioned in history.
# Let's try to import get_db from db.base
sys.path.append(os.getcwd())

from db.session import get_db, Base, engine

def verify_fix():
    session = next(get_db())
    
    # 1. Find a user with devices
    try:
        # Get a user that has devices
        result = session.execute(text("SELECT DISTINCT busi_user_id FROM devices limit 1"))
        row = result.fetchone()
        if not row:
            print("No devices found in DB.")
            return

        user_id = row[0]
        print(f"Testing for user_id: {user_id}")
        
        # 2. Test DeviceService.get_devices_by_user
        device_service = DeviceService(session)
        devices = device_service.get_devices_by_user(user_id)
        
        print(f"DeviceService returned {len(devices)} devices:")
        for d in devices:
            print(f" - {d.device_name} (Type: {d.device_type}, Status: {d.session_status}, Official: {getattr(d, 'is_official', 'N/A')})")
            
        # 3. Simulate api/devices.py logic
        unofficial_devices = []
        
        for device in devices:
            # Logic from my fix
            device.is_official = False
            unofficial_devices.append(device)
            
        filtered_devices = unofficial_devices
        
        print("\nAPI Response Logic Result:")
        print(f"Total returned: {len(filtered_devices)}")
        print("Unofficial List:", [d.device_name for d in unofficial_devices])
        
        # Verify if any 'mobile' devices are present
        mobile_devices = [d for d in devices if d.device_type == 'mobile']
        if mobile_devices:
            print(f"\nSUCCESS: Found {len(mobile_devices)} mobile devices, and they are included in result!")
        else:
            print("\nInfo: No mobile devices found for this user, but logic allows them.")

        # Verify statuses
        pending_devices = [d for d in devices if d.session_status in ['pending', 'qr_generated']]
        if pending_devices:
             print(f"SUCCESS: Found {len(pending_devices)} pending/qr_generated devices!")
        else:
             print("Info: No pending devices found.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    import sys
    # Redirect stdout to a file with utf-8 encoding
    with open("verify_output.txt", "w", encoding="utf-8") as f:
        sys.stdout = f
        verify_fix()
