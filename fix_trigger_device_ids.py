#!/usr/bin/env python3
"""
Fix device_id data inconsistency in Google Sheet triggers
Converts string device_ids to proper UUIDs or removes invalid triggers
"""

from db.session import SessionLocal
from models.google_sheet import GoogleSheetTrigger
from models.device import Device
import uuid

def fix_trigger_device_ids():
    """Fix device_id data in triggers"""
    db = SessionLocal()
    
    try:
        # Get all triggers
        triggers = db.query(GoogleSheetTrigger).all()
        print(f"Found {len(triggers)} triggers to check")
        
        fixed_count = 0
        deleted_count = 0
        
        for trigger in triggers:
            device_id = trigger.device_id
            
            # Skip if already a valid UUID
            if isinstance(device_id, uuid.UUID):
                continue
                
            # Try to convert string to UUID
            if isinstance(device_id, str):
                try:
                    # Check if it's a valid UUID string
                    uuid_obj = uuid.UUID(device_id)
                    trigger.device_id = uuid_obj
                    fixed_count += 1
                    print(f"Fixed trigger {trigger.trigger_id}: {device_id} -> {uuid_obj}")
                except ValueError:
                    # Not a valid UUID, try to find device by string (legacy data)
                    device = db.query(Device).filter(Device.device_id == device_id).first()
                    if device:
                        trigger.device_id = device.device_id
                        fixed_count += 1
                        print(f"Fixed trigger {trigger.trigger_id}: mapped to device {device.device_id}")
                    else:
                        # Delete trigger with invalid device_id
                        print(f"Deleting trigger {trigger.trigger_id}: invalid device_id {device_id}")
                        db.delete(trigger)
                        deleted_count += 1
        
        # Commit changes
        db.commit()
        print(f"\n✅ Fix completed:")
        print(f"   Fixed: {fixed_count} triggers")
        print(f"   Deleted: {deleted_count} triggers")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error fixing triggers: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    fix_trigger_device_ids()
