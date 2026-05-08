#!/usr/bin/env python3
"""
Remove dummy/mock messages and show only real WhatsApp messages
"""

import logging
from sqlalchemy import text
from db.session import SessionLocal
from models.whatsapp_inbox import WhatsAppInbox

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_dummy_messages():
    """Remove dummy/mock messages from database"""
    db = SessionLocal()
    try:
        logger.info("🧹 CLEANING DUMMY/MOCK MESSAGES")
        logger.info("=" * 50)
        
        # Check for dummy/mock patterns
        dummy_patterns = [
            "TEST", "MOCK", "DUMMY", "DEBUG", "SAMPLE", 
            "Hello from test", "TRIGGER TEST", "MANUAL TEST",
            "POST /api/", "GET /api/", "REAL-TIME TRIGGER"
        ]
        
        total_messages = 0
        removed_messages = 0
        
        # Check all messages
        all_messages = db.query(WhatsAppInbox).all()
        total_messages = len(all_messages)
        
        logger.info(f"📊 Total messages in database: {total_messages}")
        
        # Find and remove dummy messages
        for msg in all_messages:
            is_dummy = False
            reason = ""
            
            # Check message content for dummy patterns
            if msg.incoming_message:
                for pattern in dummy_patterns:
                    if pattern in msg.incoming_message.upper():
                        is_dummy = True
                        reason = f"Contains '{pattern}'"
                        break
            
            # Check phone numbers that look like test numbers
            if msg.phone_number:
                # Common test phone patterns
                if (msg.phone_number in ["1234567890", "9876543210", "0000000000"] or
                    msg.phone_number.startswith("000") or
                    len(msg.phone_number) < 10 or len(msg.phone_number) > 15):
                    is_dummy = True
                    reason = f"Test phone number: {msg.phone_number}"
            
            # Check for system-generated messages
            if msg.incoming_message and ("POST /api/" in msg.incoming_message or 
                                       "GET /api/" in msg.incoming_message):
                is_dummy = True
                reason = "System/API message"
            
            if is_dummy:
                logger.info(f"🗑️  Removing dummy message: {msg.id}")
                logger.info(f"   Reason: {reason}")
                logger.info(f"   Phone: {msg.phone_number}")
                logger.info(f"   Message: {msg.incoming_message[:50]}...")
                db.delete(msg)
                removed_messages += 1
        
        # Commit changes
        if removed_messages > 0:
            db.commit()
            logger.info(f"✅ Removed {removed_messages} dummy messages")
        else:
            logger.info("✅ No dummy messages found")
        
        # Show remaining real messages
        remaining_messages = db.query(WhatsAppInbox).count()
        logger.info(f"📱 Remaining real messages: {remaining_messages}")
        
        # Show sample of real messages
        real_messages = db.query(WhatsAppInbox).limit(5).all()
        logger.info("\n📋 Sample of real messages:")
        for msg in real_messages:
            logger.info(f"  📬 {msg.contact_name} ({msg.phone_number})")
            logger.info(f"     {msg.incoming_message[:50]}...")
            logger.info(f"     Time: {msg.incoming_time}")
            logger.info(f"     Unread: {not msg.is_read}")
            logger.info("---")
        
        return {
            "total_messages": total_messages,
            "removed_messages": removed_messages,
            "remaining_messages": remaining_messages
        }
        
    except Exception as e:
        logger.error(f"❌ Error cleaning dummy messages: {e}")
        db.rollback()
        return None
    finally:
        db.close()

def check_real_message_sources():
    """Check if messages are coming from real WhatsApp sources"""
    db = SessionLocal()
    try:
        logger.info("\n🔍 CHECKING REAL MESSAGE SOURCES")
        logger.info("=" * 50)
        
        # Check message sources by device
        from sqlalchemy import func
        
        device_stats = db.query(
            WhatsAppInbox.device_id,
            func.count(WhatsAppInbox.id).label('message_count'),
            func.max(WhatsAppInbox.incoming_time).label('last_message')
        ).group_by(WhatsAppInbox.device_id).all()
        
        logger.info("📱 Messages by device:")
        for stat in device_stats:
            logger.info(f"  Device {stat.device_id}: {stat.message_count} messages")
            logger.info(f"  Last message: {stat.last_message}")
            logger.info("---")
        
        # Check for real WhatsApp message IDs
        real_msg_ids = db.query(WhatsAppInbox).filter(
            WhatsAppInbox.message_id.isnot(None),
            WhatsAppInbox.message_id != ""
        ).count()
        
        logger.info(f"📧 Messages with real WhatsApp IDs: {real_msg_ids}")
        
        # Check unread real messages
        real_unread = db.query(WhatsAppInbox).filter(
            WhatsAppInbox.is_read == False,
            WhatsAppInbox.is_outgoing == False,
            WhatsAppInbox.chat_type == "individual"
        ).count()
        
        logger.info(f"📬 Real unread messages: {real_unread}")
        
        return {
            "devices_with_messages": len(device_stats),
            "real_message_ids": real_msg_ids,
            "real_unread": real_unread
        }
        
    except Exception as e:
        logger.error(f"❌ Error checking message sources: {e}")
        return None
    finally:
        db.close()

if __name__ == "__main__":
    result = clean_dummy_messages()
    check_real_message_sources()
    
    if result:
        logger.info("\n✅ DUMMY CLEANUP COMPLETED")
        logger.info(f"📊 Results: {result}")
    else:
        logger.error("❌ Dummy cleanup failed")
