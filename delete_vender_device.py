#!/usr/bin/env python3
"""
Delete the VENDER login device permanently
"""

import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()
db_url = os.getenv('DATABASE_URL')
engine = create_engine(db_url)
SessionLocal = sessionmaker(bind=engine)

def delete_vender_device():
    """Delete the VENDER login device"""
    db = SessionLocal()
    
    try:
        # Find the VENDER login device
        device_query = text("SELECT device_id, device_name FROM devices WHERE device_name = 'VENDER login'")
        result = db.execute(device_query)
        device = result.fetchone()
        
        if not device:
            logger.error("VENDER login device not found")
            return False
        
        device_id = device.device_id
        device_name = device.device_name
        
        logger.info(f"Found device: {device_name} (ID: {device_id})")
        
        # Step 1: Delete Google Sheet Trigger History (device_id is UUID)
        logger.info("Step 1: Deleting trigger history...")
        result1 = db.execute(text("DELETE FROM sheet_trigger_history WHERE device_id = CAST(:device_id AS UUID)"), {"device_id": str(device_id)})
        deleted_history = result1.rowcount
        logger.info(f"Deleted {deleted_history} trigger history records")
        
        # Step 2: Delete Google Sheet Triggers (device_id is character varying)
        logger.info("Step 2: Deleting sheet triggers...")
        result2 = db.execute(text("DELETE FROM google_sheet_triggers WHERE device_id = :device_id"), {"device_id": str(device_id)})
        deleted_triggers = result2.rowcount
        logger.info(f"Deleted {deleted_triggers} trigger records")
        
        # Step 3: Delete Google Sheets (device_id is UUID)
        logger.info("Step 3: Deleting google sheets...")
        result3 = db.execute(text("DELETE FROM google_sheets WHERE device_id = CAST(:device_id AS UUID)"), {"device_id": str(device_id)})
        deleted_sheets = result3.rowcount
        logger.info(f"Deleted {deleted_sheets} sheet records")
        
        # Step 4: Delete WhatsApp Inbox (device_id is UUID)
        logger.info("Step 4: Deleting whatsapp inbox...")
        result4 = db.execute(text("DELETE FROM whatsapp_inbox WHERE device_id = CAST(:device_id AS UUID)"), {"device_id": str(device_id)})
        deleted_inbox = result4.rowcount
        logger.info(f"Deleted {deleted_inbox} inbox records")
        
        # Step 5: Delete the device (device_id is UUID)
        logger.info("Step 5: Deleting device...")
        result5 = db.execute(text("DELETE FROM devices WHERE device_id = CAST(:device_id AS UUID)"), {"device_id": str(device_id)})
        deleted_device = result5.rowcount
        logger.info(f"Deleted {deleted_device} device record")
        
        db.commit()
        logger.info(f"✅ Device '{device_name}' permanently deleted successfully!")
        logger.info(f"Summary: {deleted_history} history, {deleted_triggers} triggers, {deleted_sheets} sheets, {deleted_inbox} inbox, {deleted_device} device records deleted")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error deleting device: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("🗑️  Deleting VENDER login device...")
    success = delete_vender_device()
    
    if success:
        print("\n✅ VENDER login device deleted successfully!")
        print("You can now add a new device from the frontend.")
    else:
        print("\n❌ Failed to delete device. Check logs above.")
