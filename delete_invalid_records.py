#!/usr/bin/env python3
"""
Delete invalid inbox records using SQL query
DELETE FROM whatsapp_inbox
WHERE length(phone_number) > 15
   OR phone_number ~ '[^0-9]';
"""

import logging
from sqlalchemy import text
from db.session import SessionLocal

logger = logging.getLogger(__name__)

def delete_invalid_records():
    """
    Delete invalid inbox records using SQL query
    """
    db = SessionLocal()
    try:
        logger.info("🗑️  DELETING INVALID INBOX RECORDS")
        logger.info("=" * 50)
        
        # Count records before deletion
        count_query = text("SELECT COUNT(*) FROM whatsapp_inbox")
        total_before = db.execute(count_query).scalar()
        logger.info(f"📊 Total records before deletion: {total_before}")
        
        # SQL query to delete invalid records
        delete_query = text("""
            DELETE FROM whatsapp_inbox 
            WHERE length(phone_number) > 15 
               OR phone_number ~ '[^0-9]'
        """)
        
        # Execute deletion
        result = db.execute(delete_query)
        deleted_count = result.rowcount
        db.commit()
        
        # Count records after deletion
        total_after = db.execute(count_query).scalar()
        
        logger.info(f"🗑️  Records deleted: {deleted_count}")
        logger.info(f"📊 Total records after deletion: {total_after}")
        
        # Show some valid records for verification
        sample_query = text("""
            SELECT phone_number, contact_name, incoming_message 
            FROM whatsapp_inbox 
            WHERE phone_number LIKE '917887640770%' 
            LIMIT 5
        """)
        
        sample_results = db.execute(sample_query).fetchall()
        if sample_results:
            logger.info(f"\n📋 SAMPLE VALID RECORDS:")
            for record in sample_results:
                logger.info(f"   Phone: {record[0]}")
                logger.info(f"   Contact: {record[1]}")
                logger.info(f"   Message: {record[2][:50]}...")
                logger.info(f"   ---")
        
        logger.info(f"\n✅ DELETION COMPLETED SUCCESSFULLY!")
        logger.info(f"   Deleted {deleted_count} invalid records")
        logger.info(f"   Remaining {total_after} valid records")
        logger.info(f"   Validity rate: {(total_after/total_before*100):.1f}%")
        
        return {
            'total_before': total_before,
            'deleted_count': deleted_count,
            'total_after': total_after,
            'validity_rate': (total_after/total_before*100) if total_before > 0 else 100
        }
        
    except Exception as e:
        logger.error(f"❌ Error during deletion: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("🚀 STARTING INVALID RECORDS DELETION")
    
    try:
        results = delete_invalid_records()
        
        logger.info(f"\n🎉 OPERATION COMPLETED!")
        logger.info(f"   Database now contains only valid MSISDN numbers")
        logger.info(f"   Ready for testing with fresh WhatsApp messages")
        
    except Exception as e:
        logger.error(f"❌ DELETION FAILED: {e}")
        exit(1)
