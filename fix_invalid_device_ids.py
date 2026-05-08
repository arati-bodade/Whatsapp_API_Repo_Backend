#!/usr/bin/env python3
"""
Fix invalid device_ids in database
"""

from db.session import SessionLocal
from sqlalchemy import text
import uuid
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_invalid_device_ids():
    """Fix invalid device_ids in triggers table"""
    db = SessionLocal()
    
    try:
        # Find all invalid device_ids
        invalid_triggers = db.execute(text('''
            SELECT trigger_id, device_id, sheet_id 
            FROM google_sheet_triggers 
            WHERE device_id NOT LIKE '%-%-%-%-%' OR LENGTH(device_id) != 36
        ''')).fetchall()
        
        logger.info(f"Found {len(invalid_triggers)} triggers with invalid device_ids")
        
        fixed_count = 0
        deleted_count = 0
        
        for trigger in invalid_triggers:
            trigger_id, device_id, sheet_id = trigger
            logger.warning(f"Invalid device_id in trigger {trigger_id}: {device_id}")
            
            # Check if this is a device- pattern that we can't fix
            if device_id.startswith('device-'):
                logger.warning(f"Deleting trigger {trigger_id} with invalid device- pattern")
                db.execute(text('DELETE FROM google_sheet_triggers WHERE trigger_id = :trigger_id'), 
                          {'trigger_id': trigger_id})
                deleted_count += 1
                continue
            
            # Try to fix other invalid formats
            try:
                # Try to parse as UUID
                uuid_obj = uuid.UUID(device_id)
                logger.info(f"Device ID {device_id} is actually valid UUID, keeping")
                fixed_count += 1
            except ValueError:
                # Not a valid UUID, delete the trigger
                logger.warning(f"Deleting trigger {trigger_id} with invalid device_id: {device_id}")
                db.execute(text('DELETE FROM google_sheet_triggers WHERE trigger_id = :trigger_id'), 
                          {'trigger_id': trigger_id})
                deleted_count += 1
        
        # Commit changes
        db.commit()
        logger.info(f"✅ Fix completed:")
        logger.info(f"   Fixed: {fixed_count} triggers")
        logger.info(f"   Deleted: {deleted_count} triggers")
        
        # Verify no more invalid device_ids
        remaining = db.execute(text('''
            SELECT COUNT(*) FROM google_sheet_triggers 
            WHERE device_id NOT LIKE '%-%-%-%-%' OR LENGTH(device_id) != 36
        ''')).scalar()
        
        logger.info(f"📊 Remaining invalid device_ids: {remaining}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error fixing device_ids: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    fix_invalid_device_ids()
