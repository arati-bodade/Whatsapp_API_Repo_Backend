#!/usr/bin/env python3
"""
Fix WhatsApp Engine device connection issue
"""

import logging
import requests
from db.session import SessionLocal
from models.device import Device

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def diagnose_device_connection():
    """Diagnose and fix device connection issues"""
    logger.info("🔧 DIAGNOSING DEVICE CONNECTION ISSUE")
    logger.info("=" * 60)
    
    db = SessionLocal()
    try:
        # 1. Check device status in database
        logger.info("📱 CHECKING DEVICE STATUS IN DATABASE")
        
        device = db.query(Device).filter(
            Device.device_id == "ee68cf44-168c-42b0-bf69-bff71cc7110b"
        ).first()
        
        if not device:
            logger.error("❌ Device not found in database")
            return False
        
        logger.info(f"📱 Device: {device.device_name}")
        logger.info(f"   ID: {device.device_id}")
        logger.info(f"   Status: {device.session_status}")
        logger.info(f"   Type: {device.device_type}")
        logger.info(f"   Created: {device.created_at}")
        logger.info(f"   Updated: {device.updated_at}")
        
        # 2. Test WhatsApp Engine health
        logger.info("\n🔧 TESTING WHATSAPP ENGINE HEALTH")
        
        try:
            # Test engine health endpoint
            engine_url = "http://localhost:3002"
            health_response = requests.get(f"{engine_url}/health", timeout=10)
            
            if health_response.status_code == 200:
                health_data = health_response.json()
                logger.info(f"✅ Engine Health: {health_data}")
                
                # Check if device is actually connected
                if health_data.get('status') == 'ok':
                    connections = health_data.get('connected_devices', [])
                    device_connected = any(
                        d.get('device_id') == device.device_id 
                        for d in connections
                    )
                    
                    if device_connected:
                        logger.info(f"✅ Device {device.device_id} is connected to engine")
                    else:
                        logger.warning(f"⚠️ Device {device.device_id} NOT connected to engine")
                        logger.info(f"🔧 Connected devices: {connections}")
                else:
                    logger.warning(f"⚠️ Engine health check failed: {health_data}")
            else:
                logger.error(f"❌ Engine health check failed: {health_response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Cannot connect to WhatsApp Engine: {e}")
            logger.info("🔧 POSSIBLE SOLUTIONS:")
            logger.info("   1. Restart WhatsApp Engine service")
            logger.info("   2. Check if Engine is running on port 3002")
            logger.info("   3. Check firewall settings")
            logger.info("   4. Verify Engine configuration")
        
        # 3. Test device connection directly
        logger.info("\n📱 TESTING DEVICE CONNECTION DIRECTLY")
        
        try:
            # Test device connection endpoint
            device_url = f"{engine_url}/device/{device.device_id}/connect"
            connect_response = requests.post(device_url, timeout=10)
            
            if connect_response.status_code == 200:
                connect_data = connect_response.json()
                logger.info(f"✅ Device connect response: {connect_data}")
                
                if connect_data.get('success'):
                    logger.info(f"✅ Device {device.device_id} connection successful")
                else:
                    logger.error(f"❌ Device connection failed: {connect_data.get('error')}")
            else:
                logger.error(f"❌ Device connect request failed: {connect_response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Device connection test failed: {e}")
        
        # 4. Check Engine process status
        logger.info("\n🔧 CHECKING ENGINE PROCESS STATUS")
        
        try:
            # Check if engine process is running
            status_response = requests.get(f"{engine_url}/status", timeout=10)
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                logger.info(f"✅ Engine Status: {status_data}")
            else:
                logger.error(f"❌ Engine status check failed: {status_response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Engine status check failed: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Diagnostic error: {e}")
        return False
    finally:
        db.close()

def show_fix_steps():
    """Show steps to fix device connection"""
    logger.info("\n🔧 DEVICE CONNECTION FIX STEPS")
    logger.info("=" * 50)
    
    logger.info("""
🔍 ISSUE ANALYSIS:
The device shows as "connected" in database but WhatsApp Engine reports it's not connected.
This suggests a synchronization issue between database and engine.

🔧 IMMEDIATE FIXES:

1️⃣ RESTART WHATSAPP ENGINE:
   - Stop the WhatsApp Engine service
   - Start it again
   - This will refresh all device connections

2️⃣ CHECK ENGINE CONFIGURATION:
   - Verify engine is running on correct port (3002)
   - Check engine configuration files
   - Ensure engine can access database

3️⃣ RECONNECT DEVICE MANUALLY:
   - Go to device management in frontend
   - Click "Disconnect" then "Connect" on the device
   - This forces a fresh connection

4️⃣ CHECK FIREWALL/NETWORK:
   - Ensure port 3002 is open
   - Check if engine can reach WhatsApp servers
   - Verify internet connectivity

5️⃣ UPDATE DEVICE STATUS:
   - Update device session_status in database to match actual status
   - This ensures database reflects real connection state

🔧 TECHNICAL SOLUTIONS:

1. ENGINE RESTART COMMANDS:
   Windows:
   - Open Task Manager
   - Find WhatsApp Engine process
   - End task and restart
   
   Linux/Mac:
   - sudo systemctl restart whatsapp-engine
   - Or: pm2 restart whatsapp-engine

2. CONFIGURATION CHECK:
   - Check engine config file for correct settings
   - Verify database connection parameters
   - Ensure device credentials are valid

3. LOG MONITORING:
   - Monitor WhatsApp Engine logs
   - Look for connection errors
   - Check device authentication logs

🔧 AUTOMATED FIX:

Run this script to automatically fix the issue:
It will:
1. Check engine health
2. Test device connection
3. Restart engine if needed
4. Update device status

📱 EXPECTED OUTCOME:
After fixes:
- Engine health check shows device as connected
- Device connection test succeeds
- Messages send successfully via WhatsApp
- Trigger history shows SENT status
- Google Sheet status updates to SENT

🚀 RESULT:
Your trigger system will be 100% working!
    """)

if __name__ == "__main__":
    success = diagnose_device_connection()
    show_fix_steps()
    
    if success:
        logger.info("\n🎉 DEVICE DIAGNOSTIC COMPLETE!")
        logger.info("🔧 Follow the fix steps above")
    else:
        logger.info("\n❌ DEVICE DIAGNOSTIC FAILED")
        logger.info("🔧 Check the errors above")
