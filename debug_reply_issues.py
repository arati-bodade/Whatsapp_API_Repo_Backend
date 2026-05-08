#!/usr/bin/env python3
"""
Debug script to identify reply message issues
"""

import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy import text
from db.session import SessionLocal
from models.whatsapp_inbox import WhatsAppInbox
from models.device import Device

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_reply_issues():
    """Debug reply message issues"""
    db = SessionLocal()
    try:
        logger.info("🔍 DEBUGGING REPLY ISSUES")
        logger.info("=" * 50)
        
        # 1. Check recent messages (last 1 hour)
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        
        recent_messages = db.query(WhatsAppInbox).filter(
            WhatsAppInbox.incoming_time >= one_hour_ago
        ).order_by(WhatsAppInbox.incoming_time.desc()).limit(10).all()
        
        logger.info(f"📊 Recent messages (last hour): {len(recent_messages)}")
        for msg in recent_messages:
            logger.info(f"  ID: {msg.id}")
            logger.info(f"  Phone: {msg.phone_number}")
            logger.info(f"  Message: {msg.incoming_message[:50]}...")
            logger.info(f"  Is Outgoing: {msg.is_outgoing}")
            logger.info(f"  Is Replied: {msg.is_replied}")
            logger.info(f"  Device: {msg.device_id}")
            logger.info(f"  Time: {msg.incoming_time}")
            logger.info("---")
        
        # 2. Check for any invalid phone numbers
        invalid_phones = db.query(WhatsAppInbox).filter(
            WhatsAppInbox.phone_number.like('%@%') |
            (WhatsAppInbox.phone_number.length() > 20) |
            (WhatsAppInbox.phone_number.length() < 10)
        ).count()
        
        logger.info(f"⚠️  Invalid phone numbers found: {invalid_phones}")
        
        # 3. Check device status
        devices = db.query(Device).filter(
            Device.device_type == 'web'
        ).all()
        
        logger.info(f"📱 Web devices: {len(devices)}")
        for device in devices:
            logger.info(f"  Device ID: {device.device_id}")
            logger.info(f"  Status: {device.session_status}")
            logger.info(f"  Connected: {device.connected_at}")
            logger.info(f"  Disconnected: {device.disconnected_at}")
            logger.info("---")
        
        # 4. Check for any cleanup script evidence
        logger.info("🔍 Checking for potential cleanup script activity...")
        
        # Check if messages are being deleted by looking at message ID patterns
        message_ids = db.query(WhatsAppInbox.message_id).filter(
            WhatsAppInbox.message_id.isnot(None)
        ).limit(10).all()
        
        logger.info(f"📋 Sample message IDs: {[mid[0] for mid in message_ids if mid[0]]}")
        
        # 5. Check database size
        total_messages = db.query(WhatsAppInbox).count()
        logger.info(f"📊 Total messages in inbox: {total_messages}")
        
        # 6. Check outgoing vs incoming ratio
        outgoing_count = db.query(WhatsAppInbox).filter(
            WhatsAppInbox.is_outgoing == True
        ).count()
        
        incoming_count = db.query(WhatsAppInbox).filter(
            WhatsAppInbox.is_outgoing == False
        ).count()
        
        logger.info(f"📈 Outgoing messages: {outgoing_count}")
        logger.info(f"📈 Incoming messages: {incoming_count}")
        
        if outgoing_count == 0 and incoming_count > 0:
            logger.warning("⚠️  No outgoing messages found - replies may not be saving correctly!")
        
        return {
            "recent_messages": len(recent_messages),
            "invalid_phones": invalid_phones,
            "total_messages": total_messages,
            "outgoing_count": outgoing_count,
            "incoming_count": incoming_count
        }
        
    except Exception as e:
        logger.error(f"❌ Debug error: {e}")
        return None
    finally:
        db.close()

if __name__ == "__main__":
    results = debug_reply_issues()
    if results:
        logger.info("✅ Debug completed successfully")
        logger.info(f"Results: {results}")
    else:
        logger.error("❌ Debug failed")
