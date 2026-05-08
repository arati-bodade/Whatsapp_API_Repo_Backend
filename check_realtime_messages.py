#!/usr/bin/env python3
"""
Check real-time WhatsApp message reception and webhook status
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

def check_realtime_messages():
    """Check for real-time WhatsApp messages"""
    db = SessionLocal()
    try:
        logger.info("📱 CHECKING REAL-TIME WHATSAPP MESSAGES")
        logger.info("=" * 50)
        
        # Check messages from last 24 hours (real recent activity)
        last_24h = datetime.now(timezone.utc) - timedelta(hours=24)
        recent_messages = db.query(WhatsAppInbox).filter(
            WhatsAppInbox.incoming_time >= last_24h
        ).order_by(WhatsAppInbox.incoming_time.desc()).all()
        
        logger.info(f"📊 Messages in last 24 hours: {len(recent_messages)}")
        
        # Show recent real messages
        logger.info("\n📋 Recent real messages (last 24h):")
        for i, msg in enumerate(recent_messages[:10]):
            logger.info(f"  {i+1}. 📬 {msg.contact_name} ({msg.phone_number})")
            logger.info(f"     Message: {msg.incoming_message[:50]}...")
            logger.info(f"     Time: {msg.incoming_time}")
            logger.info(f"     Device: {msg.device_id}")
            logger.info(f"     Unread: {not msg.is_read}")
            logger.info(f"     Outgoing: {msg.is_outgoing}")
            logger.info("---")
        
        # Check unread real messages
        unread_real = db.query(WhatsAppInbox).filter(
            WhatsAppInbox.is_read == False,
            WhatsAppInbox.is_outgoing == False,
            WhatsAppInbox.chat_type == "individual"
        ).order_by(WhatsAppInbox.incoming_time.desc()).all()
        
        logger.info(f"\n📬 Real unread messages: {len(unread_real)}")
        for i, msg in enumerate(unread_real[:5]):
            logger.info(f"  {i+1}. 📬 {msg.contact_name} ({msg.phone_number})")
            logger.info(f"     Message: {msg.incoming_message[:50]}...")
            logger.info(f"     Time: {msg.incoming_time}")
            logger.info(f"     Device: {msg.device_id}")
            logger.info("---")
        
        # Check connected devices for real-time reception
        connected_devices = db.query(Device).filter(
            Device.session_status == "connected",
            Device.device_type == "web"
        ).all()
        
        logger.info(f"\n🔗 Connected devices for real-time: {len(connected_devices)}")
        for device in connected_devices:
            logger.info(f"  📱 Device: {device.device_id}")
            logger.info(f"     Status: {device.session_status}")
            logger.info(f"     Last Active: {device.last_active}")
            logger.info("---")
        
        return {
            "recent_24h": len(recent_messages),
            "unread_real": len(unread_real),
            "connected_devices": len(connected_devices)
        }
        
    except Exception as e:
        logger.error(f"❌ Error checking real-time messages: {e}")
        return None
    finally:
        db.close()

def test_webhook_reception():
    """Test if webhook can receive real messages"""
    logger.info("\n🌐 TESTING WEBHOOK RECEPTION")
    logger.info("=" * 50)
    
    # Test webhook endpoint
    webhook_url = "http://localhost:8000/api/webhooks/whatsapp/incoming"
    
    # Create a realistic WhatsApp message payload
    real_payload = {
        "device_id": "550e8400-e29b-41d4-a716-446655440000",
        "remoteJid": "919876543210@s.whatsapp.net",
        "phone": "919876543210",
        "message": "Real test message from webhook",
        "push_name": "Real Contact",
        "timestamp": int(datetime.now().timestamp()),
        "from_me": False,
        "message_id": "real_msg_123456789"
    }
    
    try:
        logger.info("📤 Sending test message to webhook...")
        response = requests.post(webhook_url, json=real_payload, timeout=10)
        
        if response.status_code == 200:
            logger.info("✅ Webhook received message successfully")
            logger.info(f"   Response: {response.json()}")
            return True
        else:
            logger.error(f"❌ Webhook failed with status: {response.status_code}")
            logger.error(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Webhook test failed: {e}")
        return False

def check_whatsapp_engine_status():
    """Check WhatsApp engine connection status"""
    logger.info("\n🔧 CHECKING WHATSAPP ENGINE STATUS")
    logger.info("=" * 50)
    
    # Check if there are any recent message IDs (indicates engine is working)
    db = SessionLocal()
    try:
        recent_with_ids = db.query(WhatsAppInbox).filter(
            WhatsAppInbox.message_id.isnot(None),
            WhatsAppInbox.message_id != "",
            WhatsAppInbox.incoming_time >= datetime.now(timezone.utc) - timedelta(hours=1)
        ).count()
        
        logger.info(f"📧 Messages with WhatsApp IDs (last hour): {recent_with_ids}")
        
        if recent_with_ids > 0:
            logger.info("✅ WhatsApp engine appears to be sending messages")
        else:
            logger.info("⚠️  No recent messages from WhatsApp engine")
            logger.info("   Possible issues:")
            logger.info("   - WhatsApp engine not running")
            logger.info("   - Webhook URL not configured in engine")
            logger.info("   - Devices not connected to engine")
            logger.info("   - Network connectivity issues")
        
        return recent_with_ids > 0
        
    except Exception as e:
        logger.error(f"❌ Error checking engine status: {e}")
        return False
    finally:
        db.close()

def show_realtime_setup_guide():
    """Show how to ensure real-time messages work"""
    logger.info("\n🚀 REAL-TIME SETUP GUIDE")
    logger.info("=" * 50)
    
    logger.info("📋 To ensure real messages show in frontend:")
    logger.info("""
1. WhatsApp Engine Configuration:
   - Set webhook URL to: http://your-server:8000/api/webhooks/whatsapp/incoming
   - Ensure devices are connected to engine
   - Check engine logs for message sending

2. Device Connection:
   - Connect mobile devices to WhatsApp engine
   - Verify device status shows "connected"
   - Test with real WhatsApp messages

3. Frontend Integration:
   - Use /replies/unread-messages for real unread
   - Use /replies/unread-count for badges
   - Poll every 30 seconds for real-time updates

4. Message Verification:
   - Check message_id exists (real WhatsApp ID)
   - Verify phone numbers are real
   - Ensure chat_type == "individual"
    """)

if __name__ == "__main__":
    results = check_realtime_messages()
    webhook_ok = test_webhook_reception()
    engine_ok = check_whatsapp_engine_status()
    show_realtime_setup_guide()
    
    logger.info("\n✅ REAL-TIME CHECK COMPLETED")
    if results:
        logger.info(f"📊 Results: {results}")
    logger.info(f"🌐 Webhook: {'✅ Working' if webhook_ok else '❌ Failed'}")
    logger.info(f"🔧 Engine: {'✅ Active' if engine_ok else '❌ Inactive'}")
