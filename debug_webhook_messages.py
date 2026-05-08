#!/usr/bin/env python3
"""
Debug script to check incoming WhatsApp messages and webhook functionality
"""

import logging
import requests
import json
from datetime import datetime, timezone, timedelta
from sqlalchemy import text
from db.session import SessionLocal
from models.whatsapp_inbox import WhatsAppInbox
from models.device import Device

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_incoming_messages():
    """Debug incoming messages and webhook issues"""
    db = SessionLocal()
    try:
        logger.info("🔍 DEBUGGING INCOMING MESSAGES")
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
            logger.info(f"  Is Incoming: {not msg.is_outgoing}")
            logger.info(f"  Is Read: {msg.is_read}")
            logger.info(f"  Device: {msg.device_id}")
            logger.info(f"  Time: {msg.incoming_time}")
            logger.info("---\n")
        
        # 2. Check unread messages
        unread_messages = db.query(WhatsAppInbox).filter(
            WhatsAppInbox.is_read == False,
            WhatsAppInbox.is_outgoing == False
        ).order_by(WhatsAppInbox.incoming_time.desc()).limit(10).all()
        
        logger.info(f"📬 Unread messages: {len(unread_messages)}")
        for msg in unread_messages:
            logger.info(f"  ID: {msg.id}")
            logger.info(f"  Phone: {msg.phone_number}")
            logger.info(f"  Message: {msg.incoming_message[:50]}...")
            logger.info(f"  Device: {msg.device_id}")
            logger.info(f"  Time: {msg.incoming_time}")
            logger.info("---\n")
        
        # 3. Check connected devices
        devices = db.query(Device).filter(
            Device.device_type == 'web'
        ).all()
        
        logger.info(f"📱 Web devices: {len(devices)}")
        for device in devices:
            logger.info(f"  Device ID: {device.device_id}")
            logger.info(f"  Status: {device.session_status}")
            logger.info(f"  Last Active: {device.last_active}")
            logger.info(f"  Disconnected: {device.disconnected_at}")
            logger.info("---\n")
        
        # 4. Test webhook endpoint
        logger.info("🌐 Testing webhook endpoint...")
        try:
            webhook_url = "http://localhost:8000/api/webhooks/whatsapp/incoming"
            test_payload = {
                "device_id": "550e8400-e29b-41d4-a716-446655440000",
                "remoteJid": "919876543210@s.whatsapp.net",
                "phone": "919876543210",
                "message": "Test message from debug script",
                "push_name": "Test Contact",
                "timestamp": int(datetime.now().timestamp()),
                "from_me": False
            }
            
            response = requests.post(webhook_url, json=test_payload, timeout=10)
            logger.info(f"  Webhook response: {response.status_code}")
            logger.info(f"  Webhook body: {response.text}")
            
        except Exception as e:
            logger.error(f"  Webhook test failed: {e}")
        
        # 5. Check database connection
        logger.info("🗄️ Testing database connection...")
        try:
            result = db.execute(text("SELECT COUNT(*) FROM whatsapp_inbox"))
            count = result.scalar()
            logger.info(f"  Total messages in database: {count}")
        except Exception as e:
            logger.error(f"  Database test failed: {e}")
        
        return {
            "recent_messages": len(recent_messages),
            "unread_messages": len(unread_messages),
            "total_devices": len(devices),
            "webhook_test": "success" if 'response' in locals() else "failed"
        }
        
    except Exception as e:
        logger.error(f"❌ Debug error: {e}")
        return None
    finally:
        db.close()

def check_webhook_reception():
    """Check if webhook is receiving messages from WhatsApp engine"""
    logger.info("🔍 CHECKING WEBHOOK RECEPTION")
    logger.info("=" * 50)
    
    # Check if WhatsApp engine is sending webhooks
    possible_issues = [
        "1. WhatsApp engine not configured to send webhooks to this server",
        "2. Webhook URL not accessible from WhatsApp engine",
        "3. Device not connected to WhatsApp engine",
        "4. Messages coming from mobile but not through engine",
        "5. Webhook endpoint not properly registered"
    ]
    
    for issue in possible_issues:
        logger.info(f"⚠️  {issue}")
    
    logger.info("\n🔧 SOLUTIONS:")
    logger.info("1. Check WhatsApp engine webhook configuration")
    logger.info("2. Verify device connection status")
    logger.info("3. Test webhook with sample payload")
    logger.info("4. Check network connectivity")
    logger.info("5. Review device logs")

if __name__ == "__main__":
    results = debug_incoming_messages()
    check_webhook_reception()
    
    if results:
        logger.info("✅ Debug completed successfully")
        logger.info(f"Results: {results}")
    else:
        logger.error("❌ Debug failed")
