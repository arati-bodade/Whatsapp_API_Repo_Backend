#!/usr/bin/env python3
"""
Safe fix for device_id data inconsistency using raw SQL
"""

from db.session import SessionLocal
from sqlalchemy import text
import uuid

def fix_trigger_device_ids():
    """Fix device_id data in triggers using raw SQL"""
    db = SessionLocal()
    
    try:
        print("Checking trigger device_id issues...")
        
        # First, let's see what devices we have
        devices = db.execute(text("SELECT device_id, device_name FROM devices")).fetchall()
        print(f"Found {len(devices)} devices:")
        for device in devices:
            print(f"  {device[0]} - {device[1]}")
        
        # Get all triggers with their device_ids
        triggers = db.execute(text("SELECT trigger_id, device_id, sheet_id FROM google_sheet_triggers")).fetchall()
        print(f"\nFound {len(triggers)} triggers:")
        
        fixed_count = 0
        deleted_count = 0
        
        for trigger in triggers:
            trigger_id, device_id, sheet_id = trigger
            
            # Skip if already valid UUID (length check)
            if len(str(device_id)) == 36 and '-' in str(device_id):
                print(f"  Trigger {trigger_id}: device_id already valid UUID")
                continue
                
            print(f"  Trigger {trigger_id}: invalid device_id '{device_id}'")
            
            # Try to find a valid device to assign
            if devices:
                # Assign the first available device
                valid_device_id = devices[0][0]
                print(f"    -> Assigning valid device: {valid_device_id}")
                
                db.execute(
                    text("UPDATE google_sheet_triggers SET device_id = :device_id WHERE trigger_id = :trigger_id"),
                    {"device_id": valid_device_id, "trigger_id": trigger_id}
                )
                fixed_count += 1
            else:
                # No devices available, delete the trigger
                print(f"    -> No valid devices available, deleting trigger")
                db.execute(
                    text("DELETE FROM google_sheet_triggers WHERE trigger_id = :trigger_id"),
                    {"trigger_id": trigger_id}
                )
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
