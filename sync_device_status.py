#!/usr/bin/env python3
"""
Fix device synchronization between database and WhatsApp Engine
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.device import Device, SessionStatus
from services.whatsapp_engine_service import WhatsAppEngineService
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost/whatsapp_platform')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

def sync_all_devices():
    """Sync all devices with WhatsApp Engine"""
    logger.info("Starting device synchronization...")
    
    engine_service = WhatsAppEngineService(db)
    devices = db.query(Device).all()
    
    for device in devices:
        logger.info(f"Syncing device: {device.device_id} ({device.device_name})")
        
        # Check actual status in engine
        device_status = engine_service.check_device_status(str(device.device_id))
        engine_status = device_status.get("status")
        
        logger.info(f"Engine status for {device.device_id}: {engine_status}")
        
        # Update database based on actual engine status
        if engine_status == "connected":
            new_status = SessionStatus.connected
            logger.info(f"Device {device.device_id} is connected in engine")
        elif engine_status == "qr_ready":
            new_status = SessionStatus.qr_generated
            logger.info(f"Device {device.device_id} has QR ready")
        elif engine_status == "connecting":
            new_status = SessionStatus.connecting
            logger.info(f"Device {device.device_id} is connecting")
        else:  # not_found, disconnected, error, etc.
            new_status = SessionStatus.disconnected
            logger.info(f"Device {device.device_id} is not connected (status: {engine_status})")
        
        # Update device status if changed
        if device.session_status != new_status:
            old_status = device.session_status
            device.session_status = new_status
            device.last_active = datetime.utcnow()
            db.commit()
            logger.info(f"Device {device.device_id} status updated: {old_status} -> {new_status}")
        else:
            logger.info(f"Device {device.device_id} status unchanged: {new_status}")
    
    logger.info("Device synchronization completed")

if __name__ == "__main__":
    from datetime import datetime
    sync_all_devices()
    db.close()
