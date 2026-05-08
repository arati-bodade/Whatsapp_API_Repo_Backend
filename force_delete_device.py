#!/usr/bin/env python3
"""
Force delete a device permanently - removes all references first
"""

import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import uuid

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()
db_url = os.getenv('DATABASE_URL')
engine = create_engine(db_url)
SessionLocal = sessionmaker(bind=engine)

def force_delete_device(device_identifier):
    """Force delete device by name or ID"""
    db = SessionLocal()
    
    try:
        # Find device by name or ID
        if device_identifier.replace('-', '').replace('_', '').replace(' ', '').isalnum():
            # Try as UUID
            try:
                device_uuid = uuid.UUID(device_identifier)
                device_query = text("SELECT device_id, device_name FROM devices WHERE device_id = :device_id")
                result = db.execute(device_query, {"device_id": device_uuid})
            except:
                device_query = text("SELECT device_id, device_name FROM devices WHERE device_name ILIKE :device_name")
                result = db.execute(device_query, {"device_name": f"%{device_identifier}%"})
        else:
            # Search by name
            device_query = text("SELECT device_id, device_name FROM devices WHERE device_name ILIKE :device_name")
            result = db.execute(device_query, {"device_name": f"%{device_identifier}%"})
        
        device = result.fetchone()
        if not device:
            logger.error(f"Device '{device_identifier}' not found")
            return False
        
        device_id = device.device_id
        device_name = device.device_name
        
        logger.info(f"Found device: {device_name} (ID: {device_id})")
        
        # Step 1: Delete Google Sheet Trigger History
        logger.info("Step 1: Deleting trigger history...")
        db.execute(text("DELETE FROM sheet_trigger_history WHERE device_id = :device_id::uuid"), {"device_id": device_id})
        
        # Step 2: Delete Google Sheet Triggers
        logger.info("Step 2: Deleting sheet triggers...")
        db.execute(text("DELETE FROM google_sheet_triggers WHERE device_id = :device_id::uuid"), {"device_id": device_id})
        
        # Step 3: Delete Google Sheets
        logger.info("Step 3: Deleting google sheets...")
        db.execute(text("DELETE FROM google_sheets WHERE device_id = :device_id::uuid"), {"device_id": device_id})
        
        # Step 4: Delete WhatsApp Inbox
        logger.info("Step 4: Deleting whatsapp inbox...")
        db.execute(text("DELETE FROM whatsapp_inbox WHERE device_id = :device_id::uuid"), {"device_id": device_id})
        
        # Step 5: Delete the device
        logger.info("Step 5: Deleting device...")
        db.execute(text("DELETE FROM devices WHERE device_id = :device_id::uuid"), {"device_id": device_id})
        
        db.commit()
        logger.info(f"✅ Device '{device_name}' permanently deleted successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error deleting device: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def list_devices():
    """List all devices"""
    db = SessionLocal()
    
    try:
        result = db.execute(text("""
            SELECT device_id, device_name, session_status, is_active, created_at 
            FROM devices 
            ORDER BY created_at DESC
        """))
        
        devices = result.fetchall()
        
        if not devices:
            print("No devices found")
            return
        
        print("\n📱 All Devices:")
        print("-" * 80)
        for device in devices:
            status = "🟢 ACTIVE" if device.is_active else "🔴 INACTIVE"
            print(f"Name: {device.device_name}")
            print(f"ID: {device.device_id}")
            print(f"Status: {device.session_status} ({status})")
            print(f"Created: {device.created_at}")
            print("-" * 80)
            
    finally:
        db.close()

if __name__ == "__main__":
    print("🔧 WhatsApp Device Management Tool")
    print("=" * 50)
    
    # List devices first
    list_devices()
    
    # Ask which device to delete
    device_input = input("\nEnter device name or ID to permanently delete (or 'exit' to quit): ").strip()
    
    if device_input.lower() == 'exit':
        print("Operation cancelled.")
    elif device_input:
        confirm = input(f"⚠️  Are you sure you want to permanently delete '{device_input}'? This cannot be undone! (yes/no): ").strip().lower()
        
        if confirm == 'yes':
            success = force_delete_device(device_input)
            if success:
                print("\n✅ Device deleted successfully! You can now add a new device.")
                list_devices()
            else:
                print("\n❌ Failed to delete device. Check logs for details.")
        else:
            print("Operation cancelled.")
    else:
        print("No device specified.")
