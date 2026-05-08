#!/usr/bin/env python3
"""
Clear all old wrong inbox data
DELETE FROM whatsapp_inbox;
"""

import logging
from sqlalchemy import text
from db.session import SessionLocal

logger = logging.getLogger(__name__)

def clear_all_inbox_data():
    """
    Clear all old wrong inbox data
    """
    db = SessionLocal()
    try:
        logger.info("🗑️  CLEARING ALL INBOX DATA")
        logger.info("=" * 50)
        
        # Count records before deletion
        count_query = text("SELECT COUNT(*) FROM whatsapp_inbox")
        total_before = db.execute(count_query).scalar()
        logger.info(f"📊 Total records before clearing: {total_before}")
        
        # Delete all records
        delete_query = text("DELETE FROM whatsapp_inbox")
        result = db.execute(delete_query)
        deleted_count = result.rowcount
        db.commit()
        
        # Verify deletion
        total_after = db.execute(count_query).scalar()
        
        logger.info(f"🗑️  Records deleted: {deleted_count}")
        logger.info(f"📊 Total records after clearing: {total_after}")
        
        if total_after == 0:
            logger.info("✅ INBOX COMPLETELY CLEARED!")
            logger.info("   Ready for fresh MSISDN storage")
        else:
            logger.warning(f"⚠️  {total_after} records remain")
        
        return {
            'total_before': total_before,
            'deleted_count': deleted_count,
            'total_after': total_after
        }
        
    except Exception as e:
        logger.error(f"❌ Error clearing inbox: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("🚀 STARTING INBOX DATA CLEARANCE")
    
    try:
        results = clear_all_inbox_data()
        
        logger.info(f"\n🎉 CLEARANCE COMPLETED!")
        logger.info(f"   Deleted {results['deleted_count']} records")
        logger.info(f"   Inbox is now empty")
        logger.info(f"   Ready for fresh WhatsApp messages")
        
    except Exception as e:
        logger.error(f"❌ CLEARANCE FAILED: {e}")
        exit(1)
