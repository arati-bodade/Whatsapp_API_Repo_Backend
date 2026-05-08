#!/usr/bin/env python3
"""
Check available devices in database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.session import get_db
from models.device import Device

def check_devices():
    """Check what devices are available"""
    
    print("=== Available Devices ===")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Query all devices
        devices = db.query(Device).all()
        
        print(f"Found {len(devices)} devices:")
        
        for device in devices:
            print(f"  - ID: {device.device_id}")
            print(f"    Name: {device.device_name}")
            print(f"    Status: {device.session_status}")
            print(f"    User ID: {device.busi_user_id}")
            print()
            
        if not devices:
            print("No devices found in database!")
            
    except Exception as e:
        print(f"❌ Error checking devices: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_devices()
