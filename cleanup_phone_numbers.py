#!/usr/bin/env python3
"""
Database cleanup script to fix invalid phone numbers in WhatsAppInbox table
"""

import logging
import re
from sqlalchemy.orm import Session
from db.session import SessionLocal
from models.whatsapp_inbox import WhatsAppInbox

logger = logging.getLogger(__name__)

def is_valid_phone_number(phone: str) -> bool:
    """
    Check if phone number is a valid MSISDN (digits only, length 10-15)
    """
    if not phone:
        return False
    
    # Remove all non-numeric characters
    clean_phone = re.sub(r'[^\d]', '', str(phone))
    
    # Check if it's a valid MSISDN
    return clean_phone.isdigit() and len(clean_phone) >= 10 and len(clean_phone) <= 15

def extract_phone_from_jid(remote_jid: str) -> str:
    """
    Extract phone number from remote_jid if available
    """
    if not remote_jid:
        return None
    
    # Extract phone number from JID (format: phone@s.whatsapp.net or phone@g.us)
    if "@" in remote_jid:
        phone = remote_jid.split("@")[0]
        if is_valid_phone_number(phone):
            return phone
    
    return None

def cleanup_phone_numbers():
    """
    Clean up existing WhatsAppInbox records with invalid phone numbers
    """
    db = SessionLocal()
    try:
        logger.info("🧹 Starting phone number cleanup...")
        
        # Find all records with invalid phone numbers
        invalid_records = db.query(WhatsAppInbox).all()
        invalid_count = 0
        fixed_count = 0
        
        for record in invalid_records:
            phone_needs_fix = not is_valid_phone_number(record.phone_number)
            
            if phone_needs_fix:
                invalid_count += 1
                logger.info(f"🔍 Found invalid phone: {record.phone_number} (ID: {record.id})")
                
                # Try to extract from any available JID information
                # Note: This would require additional fields in the schema or logs
                # For now, we'll mark these records for review
                
                # Option 1: If we have access to webhook logs, we could extract from there
                # Option 2: Mark as invalid for manual review
                
                logger.warning(f"⚠️  Record {record.id} has invalid phone number: {record.phone_number}")
                
                # For now, we'll just log these records
                # In a real scenario, you might want to:
                # 1. Cross-reference with webhook logs
                # 2. Contact the user to verify
                # 3. Delete records that are clearly invalid (like WhatsApp service IDs)
        
        logger.info(f"📊 Cleanup Summary:")
        logger.info(f"   Total records checked: {len(invalid_records)}")
        logger.info(f"   Invalid phone numbers found: {invalid_count}")
        logger.info(f"   Records fixed: {fixed_count}")
        
        if invalid_count > 0:
            logger.warning(f"⚠️  {invalid_count} records still have invalid phone numbers")
            logger.info("💡 Recommendation: Review these records manually or cross-reference with webhook logs")
        else:
            logger.info("✅ All phone numbers are valid!")
            
    except Exception as e:
        logger.error(f"❌ Error during cleanup: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def delete_whatsapp_service_ids():
    """
    Delete records that are clearly WhatsApp service IDs (starting with 120363)
    """
    db = SessionLocal()
    try:
        logger.info("🗑️  Deleting WhatsApp service ID records...")
        
        # Find and delete records with WhatsApp service IDs
        service_records = db.query(WhatsAppInbox).filter(
            WhatsAppInbox.phone_number.like("120363%")
        ).all()
        
        deleted_count = len(service_records)
        
        for record in service_records:
            logger.info(f"🗑️  Deleting service ID record: {record.phone_number} (ID: {record.id})")
            db.delete(record)
        
        db.commit()
        
        logger.info(f"✅ Deleted {deleted_count} WhatsApp service ID records")
        
    except Exception as e:
        logger.error(f"❌ Error deleting service records: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    logger.info("🚀 Starting WhatsApp phone number cleanup...")
    
    # First delete obvious service IDs
    delete_whatsapp_service_ids()
    
    # Then analyze remaining records
    cleanup_phone_numbers()
    
    logger.info("✅ Cleanup completed!")
