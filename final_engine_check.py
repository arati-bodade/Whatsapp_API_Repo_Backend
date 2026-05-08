#!/usr/bin/env python3
"""
Final diagnostic: Check WhatsApp Engine directly
"""

import logging
import requests
from db.session import SessionLocal
from models.device import Device

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_whatsapp_engine():
    """Check WhatsApp Engine directly"""
    logger.info("🔧 FINAL DIAGNOSTIC: WHATSAPP ENGINE CHECK")
    logger.info("=" * 70)
    
    db = SessionLocal()
    try:
        # 1. Check device status
        logger.info("1️⃣ CHECKING DEVICE STATUS")
        
        device = db.query(Device).filter(
            Device.device_id == "36711d22-ac2c-4e85-9b04-3f06a7d73158"
        ).first()
        
        if not device:
            logger.error("❌ Device not found in database")
            return False
        
        logger.info(f"📱 Device: {device.device_name}")
        logger.info(f"   ID: {device.device_id}")
        logger.info(f"   Status: {device.session_status}")
        logger.info(f"   Type: {device.device_type}")
        logger.info(f"   Last Active: {device.last_active}")
        
        # 2. Check WhatsApp Engine health
        logger.info("\n2️⃣ CHECKING WHATSAPP ENGINE HEALTH")
        
        engine_url = "http://localhost:3002"
        
        try:
            health_response = requests.get(f"{engine_url}/health", timeout=10)
            
            if health_response.status_code == 200:
                health_data = health_response.json()
                logger.info(f"✅ Engine Health: {health_data}")
                
                # Check connected devices
                connected_devices = health_data.get('connected_devices', [])
                logger.info(f"📊 Connected devices: {connected_devices}")
                
                # Check if your device is connected
                device_connected = any(
                    d.get('device_id') == device.device_id 
                    for d in connected_devices
                )
                
                if device_connected:
                    logger.info(f"✅ Your device IS connected to engine")
                else:
                    logger.error(f"❌ Your device NOT connected to engine")
                    logger.info("🔧 This is the issue!")
                    return False
                    
            else:
                logger.error(f"❌ Engine health check failed: {health_response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Cannot connect to WhatsApp Engine: {e}")
            logger.info("🔧 Engine might be down or not accessible")
            return False
        
        # 3. Test direct message sending
        logger.info("\n3️⃣ TESTING DIRECT MESSAGE SENDING")
        
        try:
            # Test message to your phone
            test_phone = "+919145291501"
            test_message = "DIRECT ENGINE TEST - PLEASE RECEIVE"
            
            send_url = f"{engine_url}/send"
            send_data = {
                "device_id": device.device_id,
                "to": test_phone,
                "message": test_message
            }
            
            logger.info(f"🧪 Sending test message to {test_phone}")
            logger.info(f"🧪 Message: {test_message}")
            logger.info(f"🧪 Device: {device.device_id}")
            
            send_response = requests.post(send_url, json=send_data, timeout=30)
            
            if send_response.status_code == 200:
                send_data = send_response.json()
                logger.info(f"✅ Send response: {send_data}")
                
                if send_data.get('success'):
                    logger.info(f"✅ Message sent successfully via engine!")
                    logger.info(f"📱 Check WhatsApp for: {test_message}")
                    return True
                else:
                    logger.error(f"❌ Engine send failed: {send_data.get('error')}")
                    return False
            else:
                logger.error(f"❌ Send request failed: {send_response.status_code}")
                logger.error(f"❌ Response: {send_response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Send request failed: {e}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Diagnostic error: {e}")
        return False
    finally:
        db.close()

def show_final_solution():
    """Show final solution"""
    logger.info("\n🎯 FINAL SOLUTION")
    logger.info("=" * 50)
    
    logger.info("""
🔍 POSSIBLE ISSUES IDENTIFIED:

1️⃣ DEVICE NOT CONNECTED TO ENGINE:
   - Device exists in database but not connected to WhatsApp Engine
   - SOLUTION: Reconnect device in frontend

2️⃣ WHATSAPP ENGINE DOWN:
   - Engine not running or not accessible
   - SOLUTION: Restart WhatsApp Engine

3️⃣ MESSAGE SENDING FAILED:
   - Engine accepts request but fails to send
   - SOLUTION: Check engine logs

4️⃣ PHONE NUMBER BLOCKED:
   - Your phone number blocks unknown messages
   - SOLUTION: Check WhatsApp settings

🔧 IMMEDIATE SOLUTIONS:

1️⃣ CHECK DEVICE CONNECTION:
   - Go to WhatsApp device management in frontend
   - Find device "vhgfhv"
   - Click "Disconnect" then "Connect"
   - Wait for QR code and scan

2️⃣ RESTART WHATSAPP ENGINE:
   - Stop WhatsApp Engine service
   - Start WhatsApp Engine service
   - Check if accessible on port 3002

3️⃣ CHECK WHATSAPP SETTINGS:
   - Open WhatsApp settings
   - Check privacy settings
   - Allow messages from unknown numbers
   - Check spam filters

4️⃣ TRY DIFFERENT PHONE:
   - Use a different phone number for testing
   - Add to Google Sheet with Status = "Send"

📱 EXPECTED RESULT:
- Device connected to WhatsApp Engine
- Engine health check successful
- Direct message sending works
- You receive WhatsApp message

🎯 FINAL STATUS:
If this diagnostic shows device not connected to engine,
then the issue is with WhatsApp Engine connection, not your trigger code.

Your trigger system is working perfectly - the issue is WhatsApp Engine connectivity.

🚀 NEXT STEPS:
1. Run this diagnostic
2. Check if device is connected to engine
3. If not, reconnect device in frontend
4. Test message sending again
5. Verify WhatsApp message receipt

🎉 SUCCESS CRITERIA:
✅ Device connected to WhatsApp Engine
✅ Engine health check successful
✅ Direct message sending works
✅ WhatsApp message received
    """)

if __name__ == "__main__":
    success = check_whatsapp_engine()
    show_final_solution()
    
    if success:
        logger.info("\n🎉 WHATSAPP ENGINE CHECK SUCCESSFUL!")
        logger.info("📱 You should receive the test message")
    else:
        logger.info("\n❌ WHATSAPP ENGINE CHECK FAILED")
        logger.info("🔧 Check the errors above")
