#!/usr/bin/env python3
"""
PRODUCTION LEVEL DATABASE CLEANUP
Remove inbox records with invalid phone numbers:
- Length > 15 characters
- Contains non-digit characters
"""

import logging
import re
from sqlalchemy.orm import Session
from db.session import SessionLocal
from models.whatsapp_inbox import WhatsAppInbox

logger = logging.getLogger(__name__)

def clean_invalid_phone_numbers():
    """
    Remove records with invalid phone numbers from WhatsAppInbox table
    """
    db = SessionLocal()
    try:
        logger.info("🧹 PRODUCTION CLEANUP: Starting phone number cleanup...")
        
        # Find all records
        all_records = db.query(WhatsAppInbox).all()
        total_records = len(all_records)
        
        invalid_records = []
        valid_records = 0
        
        for record in all_records:
            phone = record.phone_number
            
            # Check for invalid phone numbers
            is_invalid = False
            reason = ""
            
            if not phone:
                is_invalid = True
                reason = "Empty phone number"
            elif len(phone) > 15:
                is_invalid = True
                reason = f"Length > 15 ({len(phone)} chars)"
            elif not phone.isdigit():
                is_invalid = True
                reason = "Contains non-digit characters"
            elif len(phone) < 10:
                is_invalid = True
                reason = f"Length < 10 ({len(phone)} chars)"
            
            if is_invalid:
                invalid_records.append({
                    'id': record.id,
                    'phone': phone,
                    'reason': reason,
                    'contact_name': record.contact_name,
                    'incoming_message': record.incoming_message[:50] + "..." if record.incoming_message else None
                })
            else:
                valid_records += 1
        
        logger.info(f"📊 ANALYSIS RESULTS:")
        logger.info(f"   Total records: {total_records}")
        logger.info(f"   Valid records: {valid_records}")
        logger.info(f"   Invalid records: {len(invalid_records)}")
        
        if invalid_records:
            logger.info(f"\n🔍 INVALID RECORDS TO DELETE:")
            for record in invalid_records[:10]:  # Show first 10
                logger.info(f"   ID: {record['id']}")
                logger.info(f"   Phone: {record['phone']}")
                logger.info(f"   Reason: {record['reason']}")
                logger.info(f"   Contact: {record['contact_name']}")
                logger.info(f"   Message: {record['incoming_message']}")
                logger.info(f"   ---")
            
            if len(invalid_records) > 10:
                logger.info(f"   ... and {len(invalid_records) - 10} more")
            
            # Confirm deletion
            logger.info(f"\n⚠️  ABOUT TO DELETE {len(invalid_records)} INVALID RECORDS")
            logger.info("   This will permanently remove these records from the database")
            
            # Delete invalid records
            deleted_count = 0
            for record_info in invalid_records:
                record = db.query(WhatsAppInbox).filter(WhatsAppInbox.id == record_info['id']).first()
                if record:
                    db.delete(record)
                    deleted_count += 1
            
            db.commit()
            logger.info(f"✅ Successfully deleted {deleted_count} invalid records")
            
        else:
            logger.info("✅ No invalid records found - database is clean!")
        
        # Final summary
        remaining_records = db.query(WhatsAppInbox).count()
        logger.info(f"\n📋 FINAL SUMMARY:")
        logger.info(f"   Original records: {total_records}")
        logger.info(f"   Records deleted: {len(invalid_records)}")
        logger.info(f"   Remaining records: {remaining_records}")
        logger.info(f"   Validity rate: {(remaining_records/total_records*100):.1f}%")
        
        return {
            'total_records': total_records,
            'invalid_records': len(invalid_records),
            'deleted_records': len(invalid_records),
            'remaining_records': remaining_records
        }
        
    except Exception as e:
        logger.error(f"❌ Error during cleanup: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("🚀 STARTING PRODUCTION PHONE NUMBER CLEANUP")
    
    try:
        results = clean_invalid_phone_numbers()
        
        if results['invalid_records'] > 0:
            logger.info(f"\n🎉 CLEANUP COMPLETED SUCCESSFULLY!")
            logger.info(f"   Removed {results['invalid_records']} invalid phone records")
            logger.info(f"   Database now contains only valid MSISDN numbers")
        else:
            logger.info(f"\n✅ DATABASE ALREADY CLEAN!")
            logger.info(f"   All {results['total_records']} records have valid phone numbers")
            
    except Exception as e:
        logger.error(f"❌ CLEANUP FAILED: {e}")
        exit(1)
