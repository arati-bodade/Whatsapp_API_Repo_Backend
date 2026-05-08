#!/usr/bin/env python3
"""
Show exactly what unread messages should appear in frontend
"""

import logging
from datetime import datetime, timezone
from db.session import SessionLocal
from models.whatsapp_inbox import WhatsAppInbox
from models.device import Device

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def show_exact_unread_messages():
    """Show exactly what unread messages should appear in frontend"""
    db = SessionLocal()
    try:
        logger.info("📬 EXACT UNREAD MESSAGES FOR FRONTEND")
        logger.info("=" * 60)
        
        # Get ALL unread messages exactly like the API does
        unread_messages = db.query(WhatsAppInbox).filter(
            WhatsAppInbox.chat_type == "individual",  # ONLY individual messages, no groups
            WhatsAppInbox.is_read == False,          # Must be unread
            WhatsAppInbox.is_outgoing == False      # Only incoming messages
        ).order_by(WhatsAppInbox.incoming_time.desc()).all()
        
        logger.info(f"📊 Total unread messages: {len(unread_messages)}")
        
        # Group by device to show which device has unread messages
        device_unreads = {}
        for msg in unread_messages:
            device_id = str(msg.device_id)
            if device_id not in device_unreads:
                device_unreads[device_id] = []
            device_unreads[device_id].append(msg)
        
        logger.info(f"📱 Devices with unread messages: {len(device_unreads)}")
        
        # Show unread messages per device
        for device_id, messages in device_unreads.items():
            # Get device info
            device = db.query(Device).filter(Device.device_id == device_id).first()
            
            logger.info(f"\n📱 Device: {device_id}")
            if device:
                logger.info(f"   Name: {device.device_name}")
                logger.info(f"   Status: {device.session_status}")
                logger.info(f"   Last Active: {device.last_active}")
                logger.info(f"   Connected: {'✅' if device.session_status == 'connected' else '❌'}")
            
            logger.info(f"   📬 Unread messages: {len(messages)}")
            
            # Show each unread message
            for i, msg in enumerate(messages):
                logger.info(f"   {i+1}. 📬 {msg.contact_name} ({msg.phone_number})")
                logger.info(f"      Message: {msg.incoming_message[:60]}...")
                logger.info(f"      Time: {msg.incoming_time}")
                logger.info(f"      Message ID: {msg.message_id}")
                logger.info(f"      Chat Type: {msg.chat_type}")
        
        # Show the exact JSON response that frontend should receive
        logger.info(f"\n📋 EXACT JSON RESPONSE FOR FRONTEND:")
        logger.info("=" * 60)
        
        response_data = []
        for msg in unread_messages:
            msg_data = {
                "id": str(msg.id),
                "device_id": str(msg.device_id),
                "phone_number": msg.phone_number,
                "contact_name": msg.contact_name,
                "incoming_message": msg.incoming_message,
                "incoming_time": msg.incoming_time.isoformat() if msg.incoming_time else None,
                "is_read": msg.is_read,
                "is_replied": msg.is_replied,
                "is_outgoing": msg.is_outgoing,
                "unread": not msg.is_read and not msg.is_outgoing,
                "is_incoming": not msg.is_outgoing,
                "chat_type": msg.chat_type,
                "message_id": msg.message_id,
                "remote_jid": msg.remote_jid
            }
            response_data.append(msg_data)
        
        json_response = {
            "success": True,
            "data": response_data
        }
        
        logger.info(f"JSON Response (first 3 messages):")
        for i, msg in enumerate(response_data[:3]):
            logger.info(f"  {i+1}. {msg['contact_name']} ({msg['phone_number']})")
            logger.info(f"     Message: {msg['incoming_message'][:40]}...")
            logger.info(f"     Unread: {msg['unread']}")
            logger.info(f"     Device: {msg['device_id']}")
        
        logger.info(f"\n📱 Frontend should receive {len(response_data)} unread messages!")
        
        return {
            "total_unread": len(unread_messages),
            "devices_with_unread": len(device_unreads),
            "json_response": json_response
        }
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return None
    finally:
        db.close()

def check_mobile_device_specifically():
    """Check specifically for mobile device that scanned QR code"""
    db = SessionLocal()
    try:
        logger.info("\n📱 CHECKING MOBILE DEVICE THAT SCANNED QR")
        logger.info("=" * 60)
        
        # Look for devices that were recently active (likely your mobile device)
        from datetime import timedelta
        recent_threshold = datetime.now(timezone.utc) - timedelta(hours=2)
        
        recent_devices = db.query(Device).filter(
            Device.device_type == "web",
            Device.last_active >= recent_threshold
        ).order_by(Device.last_active.desc()).all()
        
        logger.info(f"🔥 Recently active devices (last 2 hours): {len(recent_devices)}")
        
        for device in recent_devices:
            logger.info(f"\n📱 Mobile Device Candidate: {device.device_id}")
            logger.info(f"   Name: {device.device_name}")
            logger.info(f"   Status: {device.session_status}")
            logger.info(f"   Last Active: {device.last_active}")
            logger.info(f"   Created: {device.created_at}")
            
            # Check unread messages for this specific device
            device_unread = db.query(WhatsAppInbox).filter(
                WhatsAppInbox.device_id == device.device_id,
                WhatsAppInbox.is_read == False,
                WhatsAppInbox.is_outgoing == False,
                WhatsAppInbox.chat_type == "individual"
            ).order_by(WhatsAppInbox.incoming_time.desc()).all()
            
            logger.info(f"   📬 Unread messages: {len(device_unread)}")
            
            for i, msg in enumerate(device_unread[:3]):
                logger.info(f"   {i+1}. 📬 {msg.contact_name} ({msg.phone_number})")
                logger.info(f"      Message: {msg.incoming_message[:40]}...")
                logger.info(f"      Time: {msg.incoming_time}")
        
        return recent_devices
        
    except Exception as e:
        logger.error(f"❌ Error checking mobile device: {e}")
        return None
    finally:
        db.close()

if __name__ == "__main__":
    result = show_exact_unread_messages()
    mobile_devices = check_mobile_device_specifically()
    
    logger.info("\n✅ FRONTEND UNREAD ANALYSIS COMPLETED")
    if result:
        logger.info(f"📊 Total unread for frontend: {result['total_unread']}")
        logger.info(f"📱 Devices with unread: {result['devices_with_unread']}")
    
    if mobile_devices:
        logger.info(f"📱 Recent mobile devices: {len(mobile_devices)}")
    
    logger.info("\n🚀 Frontend should call GET /api/replies/unread-messages to get these messages!")
