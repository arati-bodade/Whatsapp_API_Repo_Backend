#!/usr/bin/env python3
"""
🧨 STEP 5: DELETE DEAD DEVICES (IMPORTANT)

You have this bad device:
1d7a7df0-c8cc-4e22-b219-e45dbd65f2f0

Run SQL:
DELETE FROM devices
WHERE device_id = '1d7a7df0-c8cc-4e22-b219-e45dbd65f2f0';

Now only connected device remains.
"""
import logging
import asyncio
from sqlalchemy.orm import Session
from db.base import SessionLocal
from services.device_validator import device_validator

logger = logging.getLogger(__name__)

async def cleanup_dead_devices():
    """
    🔧 STEP 5: DEAD DEVICE CLEANUP
    
    Detect devices that no longer exist in engine
    Mark them disabled in DB or delete them
    Prevent automation loop from retrying dead devices endlessly
    """
    logger.info("🧨 STARTING DEAD DEVICE CLEANUP")
    
    db = SessionLocal()
    
    try:
        # Get all devices from database
        from models.device import Device
        devices = db.query(Device).all()
        
        logger.info(f"   Found {len(devices)} devices in database")
        
        dead_devices = []
        alive_devices = []
        
        for device in devices:
            logger.info(f"   Checking device: {device.device_id}")
            
            # Check if device exists in Engine
            engine_status = device_validator.get_device_status(device.device_id)
            
            if engine_status == "not_found":
                dead_devices.append(device)
                logger.error(f"   ❌ DEAD DEVICE: {device.device_id} (not found in Engine)")
            else:
                alive_devices.append(device)
                logger.info(f"   ✅ ALIVE DEVICE: {device.device_id} (status: {engine_status})")
        
        # Delete dead devices
        if dead_devices:
            logger.warning(f"   🗑️  Deleting {len(dead_devices)} dead devices...")
            
            for device in dead_devices:
                logger.warning(f"   Deleting: {device.device_id} - {device.device_name}")
                db.delete(device)
            
            db.commit()
            logger.info(f"   ✅ Deleted {len(dead_devices)} dead devices")
        else:
            logger.info(f"   ✅ No dead devices found")
        
        # Update alive devices status
        if alive_devices:
            logger.info(f"   🔄 Updating {len(alive_devices)} alive devices status...")
            
            for device in alive_devices:
                engine_status = device_validator.get_device_status(device.device_id)
                
                # Update device status to match engine
                if engine_status == "connected":
                    device.session_status = "connected"
                elif engine_status == "disconnected":
                    device.session_status = "disconnected"
                else:
                    device.session_status = "expired"
                
                logger.info(f"   Updated {device.device_id} → {device.session_status}")
            
            db.commit()
            logger.info(f"   ✅ Updated {len(alive_devices)} device statuses")
        
        logger.info("🏁 DEAD DEVICE CLEANUP COMPLETE")
        
        return {
            "success": True,
            "dead_devices": len(dead_devices),
            "alive_devices": len(alive_devices)
        }
        
    except Exception as e:
        logger.error(f"❌ DEAD DEVICE CLEANUP ERROR: {e}")
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()

def manual_cleanup_sql():
    """
    Manual SQL cleanup for the specific dead device
    """
    dead_device_id = "1d7a7df0-c8cc-4e22-b219-e45dbd65f2f0"
    
    sql = f"""
    -- Delete the specific dead device
    DELETE FROM devices 
    WHERE device_id = '{dead_device_id}';
    
    -- Verify deletion
    SELECT COUNT(*) as remaining_devices FROM devices;
    """
    
    print("🧨 MANUAL SQL CLEANUP:")
    print("=" * 50)
    print(sql)
    print("=" * 50)
    print(f"   Target device: {dead_device_id}")
    print("   Run this SQL in your PostgreSQL client")

if __name__ == "__main__":
    print("🧨 DEAD DEVICE CLEANUP")
    print("=" * 50)
    print("Choose cleanup method:")
    print("1. Automatic cleanup (recommended)")
    print("2. Manual SQL cleanup")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        print("\n🔄 Running automatic cleanup...")
        asyncio.run(cleanup_dead_devices())
    elif choice == "2":
        print("\n📝 Manual SQL cleanup:")
        manual_cleanup_sql()
    else:
        print("❌ Invalid choice")
