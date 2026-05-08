import sys
import os
import logging
from sqlalchemy.orm import Session
from db.base import SessionLocal
from services.device_service import DeviceService
from models.device import Device, DeviceType, SessionStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def wipe_all_unofficial_devices():
    """
    Force logout all Unofficial (Web / QR) devices.
    Clear all engine sessions.
    Soft-delete all those devices from DB.
    """
    db: Session = SessionLocal()
    try:
        device_service = DeviceService(db)
        
        # Fetch all unofficial devices (ignoring is_active=True because we want to wipe even latent ones if possible, 
        # but logout_device handles cleanup. actually better to find ALL web devices)
        
        logger.info("SEARCHING FOR UNOFFICIAL DEVICES TO WIPE...")
        
        # We query directly to get everything including soft-deleted ones if we want to be thorough, 
        # but the goal is to make sure active ones are gone.
        # Let's target only active ones first, as soft-deleted ones are already effectively gone.
        # But to be safe and ensure engine cleanup, let's get even logged_out ones if they have a session directory?
        # Actually, `logout_device` checks if already logged out.
        
        devices = db.query(Device).filter(
            Device.device_type == DeviceType.web
        ).all()
        
        count = len(devices)
        logger.info(f"Found {count} unofficial devices (active & inactive).")
        
        deleted_count = 0
        
        for device in devices:
            logger.info(f"Processing device {device.device_id} ({device.device_name})...")
            
            # Use logout_device to handle DB update + Engine cleanup
            result = device_service.logout_device(str(device.device_id))
            
            if result.get("success"):
                logger.info(f"✅ Successfully wiped device {device.device_id}")
                deleted_count += 1
            else:
                logger.error(f"❌ Failed to wipe device {device.device_id}: {result.get('error')}")

        logger.info(f"WIPE COMPLETE. Removed {deleted_count} unofficial devices.")
        
    except Exception as e:
        logger.error(f"Error during wipe operation: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    wipe_all_unofficial_devices()
