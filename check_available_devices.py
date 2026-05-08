import sys
sys.path.append('.')
from db.session import SessionLocal
from models.device import Device
from models.busi_user import BusiUser

db = SessionLocal()

print('=== Checking Available Devices ===')

# Get Om Lunge's account
om_lunge = db.query(BusiUser).filter(BusiUser.email == 'lungeom39@gmail.com').first()
if om_lunge:
    print(f'Om Lunge Devices:')
    
    # Check devices for this user
    devices = db.query(Device).filter(Device.busi_user_id == om_lunge.busi_user_id).all()
    
    if devices:
        for i, device in enumerate(devices):
            print(f'  {i+1}. Device ID: {device.device_id}')
            print(f'     Name: {device.device_name}')
            print(f'     Type: {device.device_type}')
            print(f'     Status: {device.session_status}')
            print(f'     Active: {device.is_active}')
            print()
            
            # Store device ID for testing
            device_id = str(device.device_id)
    else:
        print('  ❌ No devices found for Om Lunge')
        device_id = None

print(f'\n🔧 SOLUTION: Use This Device ID for Automatic Credit Deduction:')
print(f'  Device ID: {device_id}')
print(f'  Endpoint: POST /unified/messages/send')
print(f'  Request Body:')
print(f'  {{')
print(f'    "user_id": "{om_lunge.busi_user_id}",')
print(f'    "device_id": "{device_id}",')
print(f'    "to": "+1234567890",')
print(f'    "message": "Your message here",')
print(f'    "type": "text",')
print(f'    "mode": "UNOFFICIAL"')
print(f'  }}')

db.close()
