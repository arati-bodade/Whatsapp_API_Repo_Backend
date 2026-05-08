#!/usr/bin/env python3
"""
Check mobile WhatsApp device and its unread messages
"""

import logging
from datetime import datetime, timezone, timedelta
from db.session import SessionLocal
from models.device import Device
from models.whatsapp_inbox import WhatsAppInbox

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_mobile_device_status():
    """Check mobile WhatsApp device connection and messages"""
    db = SessionLocal()
    try:
        logger.info("📱 CHECKING MOBILE WHATSAPP DEVICE")
        logger.info("=" * 50)
        
        # Get all devices with their status
        devices = db.query(Device).filter(
            Device.device_type == "web"
        ).all()
        
        logger.info(f"📊 Total web devices: {len(devices)}")
        
        # Check each device's status and messages
        for device in devices:
            logger.info(f"\n📱 Device: {device.device_id}")
            logger.info(f"   Name: {device.device_name}")
            logger.info(f"   Status: {device.session_status}")
            logger.info(f"   Last Active: {device.last_active}")
            logger.info(f"   Created: {device.created_at}")
            logger.info(f"   Disconnected: {device.disconnected_at}")
            
            # Check messages for this device
            device_messages = db.query(WhatsAppInbox).filter(
                WhatsAppInbox.device_id == device.device_id
            ).order_by(WhatsAppInbox.incoming_time.desc()).limit(5).all()
            
            # Check unread messages for this device
            device_unread = db.query(WhatsAppInbox).filter(
                WhatsAppInbox.device_id == device.device_id,
                WhatsAppInbox.is_read == False,
                WhatsAppInbox.is_outgoing == False,
                WhatsAppInbox.chat_type == "individual"
            ).count()
            
            logger.info(f"   📬 Total messages: {len(device_messages)}")
            logger.info(f"   📬 Unread messages: {device_unread}")
            
            # Show recent messages for this device
            if device_messages:
                logger.info(f"   📋 Recent messages:")
                for i, msg in enumerate(device_messages[:3]):
                    logger.info(f"     {i+1}. {msg.contact_name} ({msg.phone_number})")
                    logger.info(f"        {msg.incoming_message[:30]}...")
                    logger.info(f"        {msg.incoming_time}")
                    logger.info(f"        Unread: {not msg.is_read}")
            
            logger.info("---")
        
        # Find recently active devices (likely your mobile device)
        recently_active = db.query(Device).filter(
            Device.device_type == "web",
            Device.last_active >= datetime.now(timezone.utc) - timedelta(hours=1)
        ).all()
        
        logger.info(f"\n🔥 Recently active devices (last hour): {len(recently_active)}")
        for device in recently_active:
            logger.info(f"   📱 {device.device_id} - {device.session_status}")
            logger.info(f"      Last active: {device.last_active}")
        
        return {
            "total_devices": len(devices),
            "recently_active": len(recently_active),
            "devices": [
                {
                    "id": str(device.device_id),
                    "name": device.device_name,
                    "status": device.session_status,
                    "last_active": device.last_active,
                    "unread_count": db.query(WhatsAppInbox).filter(
                        WhatsAppInbox.device_id == device.device_id,
                        WhatsAppInbox.is_read == False,
                        WhatsAppInbox.is_outgoing == False
                    ).count()
                }
                for device in devices
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Error checking mobile device: {e}")
        return None
    finally:
        db.close()

def check_mobile_unread_messages():
    """Check unread messages specifically from mobile devices"""
    db = SessionLocal()
    try:
        logger.info("\n📬 CHECKING MOBILE DEVICE UNREAD MESSAGES")
        logger.info("=" * 50)
        
        # Get all unread messages from all devices
        all_unread = db.query(WhatsAppInbox).filter(
            WhatsAppInbox.is_read == False,
            WhatsAppInbox.is_outgoing == False,
            WhatsAppInbox.chat_type == "individual"
        ).order_by(WhatsAppInbox.incoming_time.desc()).all()
        
        logger.info(f"📬 Total unread messages: {len(all_unread)}")
        
        # Group unread messages by device
        device_unreads = {}
        for msg in all_unread:
            device_id = str(msg.device_id)
            if device_id not in device_unreads:
                device_unreads[device_id] = []
            device_unreads[device_id].append(msg)
        
        logger.info(f"📱 Devices with unread messages: {len(device_unreads)}")
        
        # Show unread messages per device
        for device_id, messages in device_unreads.items():
            logger.info(f"\n📱 Device {device_id}: {len(messages)} unread")
            
            # Get device info
            device = db.query(Device).filter(Device.device_id == device_id).first()
            if device:
                logger.info(f"   Name: {device.device_name}")
                logger.info(f"   Status: {device.session_status}")
                logger.info(f"   Last Active: {device.last_active}")
            
            # Show unread messages
            for i, msg in enumerate(messages[:3]):
                logger.info(f"   {i+1}. 📬 {msg.contact_name} ({msg.phone_number})")
                logger.info(f"      Message: {msg.incoming_message[:40]}...")
                logger.info(f"      Time: {msg.incoming_time}")
                logger.info(f"      Message ID: {msg.message_id}")
        
        return device_unreads
        
    except Exception as e:
        logger.error(f"❌ Error checking mobile unread: {e}")
        return None
    finally:
        db.close()

def check_webhook_mobile_reception():
    """Check if mobile device messages are being received by webhook"""
    logger.info("\n🌐 CHECKING WEBHOOK MOBILE RECEPTION")
    logger.info("=" * 50)
    
    # Check recent messages to see if they have proper mobile characteristics
    db = SessionLocal()
    try:
        recent_messages = db.query(WhatsAppInbox).filter(
            WhatsAppInbox.incoming_time >= datetime.now(timezone.utc) - timedelta(hours=24)
        ).order_by(WhatsAppInbox.incoming_time.desc()).limit(10).all()
        
        logger.info(f"📧 Recent messages (24h): {len(recent_messages)}")
        
        mobile_indicators = []
        for msg in recent_messages:
            # Check for mobile message characteristics
            has_real_id = msg.message_id and len(msg.message_id) > 10
            real_phone = len(msg.phone_number) >= 10 and len(msg.phone_number) <= 15
            real_message = msg.incoming_message and len(msg.incoming_message.strip()) > 0
            
            is_mobile_like = has_real_id and real_phone and real_message
            
            logger.info(f"\n📱 Message: {msg.id}")
            logger.info(f"   Contact: {msg.contact_name} ({msg.phone_number})")
            logger.info(f"   Message: {msg.incoming_message[:30]}...")
            logger.info(f"   Device: {msg.device_id}")
            logger.info(f"   Message ID: {msg.message_id}")
            logger.info(f"   Mobile-like: {'✅' if is_mobile_like else '❌'}")
            
            if is_mobile_like:
                mobile_indicators.append(msg)
        
        logger.info(f"\n📱 Mobile-like messages: {len(mobile_indicators)}")
        
        if len(mobile_indicators) > 0:
            logger.info("✅ Mobile device messages are being received!")
        else:
            logger.info("⚠️  No mobile-like messages found recently")
            logger.info("   Possible issues:")
            logger.info("   - Mobile device not connected to webhook")
            logger.info("   - WhatsApp engine not forwarding mobile messages")
            logger.info("   - Webhook URL not configured for mobile device")
        
        return len(mobile_indicators) > 0
        
    except Exception as e:
        logger.error(f"❌ Error checking webhook reception: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    device_status = check_mobile_device_status()
    check_mobile_unread_messages()
    mobile_reception = check_webhook_mobile_reception()
    
    logger.info("\n✅ MOBILE DEVICE CHECK COMPLETED")
    if device_status:
        logger.info(f"📊 Device Status: {device_status}")
    logger.info(f"📱 Mobile Reception: {'✅ Working' if mobile_reception else '❌ Issues Found'}")
