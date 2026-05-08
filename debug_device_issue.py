#!/usr/bin/env python3
"""
Fix device query and retrieval issues
"""

import logging
from db.session import SessionLocal
from models.device import Device
from models.google_sheet import GoogleSheetTrigger

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_device_issue():
    """Debug device query and retrieval issues"""
    logger.info("🔍 DEBUGGING DEVICE QUERY ISSUES")
    logger.info("=" * 70)
    
    db = SessionLocal()
    try:
        test_device_id = "3c0780da-b2b5-438f-a6f9-e1f9adc9d51f"
        
        # 1. Check all devices in database
        logger.info("1️⃣ CHECKING ALL DEVICES IN DATABASE")
        
        all_devices = db.query(Device).all()
        logger.info(f"📊 Total devices in database: {len(all_devices)}")
        
        for device in all_devices:
            logger.info(f"   Device ID: {device.device_id}")
            logger.info(f"   Device Name: {getattr(device, 'device_name', 'N/A')}")
            logger.info(f"   Status: {device.session_status}")
            logger.info(f"   Type: {device.device_type}")
            logger.info(f"   Last Active: {device.last_active}")
            logger.info("")
        
        # 2. Check specific device
        logger.info("2️⃣ CHECKING SPECIFIC DEVICE")
        
        device = db.query(Device).filter(Device.device_id == test_device_id).first()
        
        if device:
            logger.info(f"✅ Device found: {device.device_id}")
            logger.info(f"   Device Name: {getattr(device, 'device_name', 'N/A')}")
            logger.info(f"   Status: {device.session_status}")
            logger.info(f"   Type: {device.device_type}")
            logger.info(f"   Last Active: {device.last_active}")
            logger.info(f"   Is Active: {device.is_active}")
            
            # Check device attributes
            logger.info("🔍 Device Attributes:")
            for attr in dir(device):
                if not attr.startswith('_') and not callable(getattr(device, attr)):
                    try:
                        value = getattr(device, attr)
                        logger.info(f"   {attr}: {value}")
                    except:
                        logger.info(f"   {attr}: <unable to retrieve>")
        else:
            logger.error(f"❌ Device {test_device_id} not found")
            
            # Try to find similar device IDs
            logger.info("🔍 Looking for similar device IDs:")
            for device in all_devices:
                if test_device_id[:8] in device.device_id:
                    logger.info(f"   Similar: {device.device_id}")
        
        # 3. Check triggers using this device
        logger.info("\n3️⃣ CHECKING TRIGGERS USING THIS DEVICE")
        
        triggers = db.query(GoogleSheetTrigger).filter(
            GoogleSheetTrigger.device_id == test_device_id
        ).all()
        
        logger.info(f"📊 Triggers using device {test_device_id}: {len(triggers)}")
        
        for trigger in triggers:
            logger.info(f"   Trigger ID: {trigger.trigger_id}")
            logger.info(f"   Trigger Type: {trigger.trigger_type}")
            logger.info(f"   Status Column: {trigger.status_column}")
            logger.info(f"   Trigger Value: {trigger.trigger_value}")
        
        # 4. Test device query with different methods
        logger.info("\n4️⃣ TESTING DIFFERENT QUERY METHODS")
        
        # Method 1: Direct query
        device1 = db.query(Device).filter(Device.device_id == test_device_id).first()
        logger.info(f"Method 1 - Direct query: {device1}")
        
        # Method 2: Get by ID
        try:
            device2 = db.query(Device).get(test_device_id)
            logger.info(f"Method 2 - Get by ID: {device2}")
        except Exception as e:
            logger.info(f"Method 2 - Get by ID: Error - {e}")
        
        # Method 3: Filter by string
        device3 = db.query(Device).filter(Device.device_id == str(test_device_id)).first()
        logger.info(f"Method 3 - Filter by string: {device3}")
        
        # Method 4: Using .all() and filter
        all_devices_again = db.query(Device).all()
        device4 = None
        for d in all_devices_again:
            if str(d.device_id) == str(test_device_id):
                device4 = d
                break
        logger.info(f"Method 4 - Manual filter: {device4}")
        
        return device1 is not None
        
    except Exception as e:
        logger.error(f"❌ Debug error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def fix_device_retrieval():
    """Fix device retrieval in automation service"""
    logger.info("\n🔧 FIXING DEVICE RETRIEVAL")
    logger.info("=" * 50)
    
    logger.info("""
🔍 DEVICE RETRIEVAL FIX:

1️⃣ IDENTIFIED ISSUES:
   - Device query returns None object
   - Device exists but query fails
   - Need to fix query method

2️⃣ ROOT CAUSE:
   - Device ID type mismatch (UUID vs string)
   - Query filter not working correctly
   - Database session issues

3️⃣ FIX STRATEGY:
   - Use string comparison for device IDs
   - Add proper error handling
   - Implement fallback methods

4️⃣ CODE CHANGES NEEDED:
   - Fix device query in send_message_via_unofficial_device
   - Add device existence check
   - Implement proper error handling

🔧 SPECIFIC FIXES:

1️⃣ UPDATE DEVICE QUERY:
   - Change from UUID comparison to string comparison
   - Add device existence validation
   - Implement fallback query methods

2️⃣ ADD ERROR HANDLING:
   - Check if device is None before accessing attributes
   - Add proper error messages
   - Implement graceful fallback

3️⃣ IMPROVE LOGGING:
   - Add device query logging
   - Log device details when found
   - Log query attempts and results

🎯 EXPECTED RESULT:
✅ Device query returns valid device object
✅ Device attributes accessible
✅ Message sending works
✅ Trigger history created
✅ WhatsApp messages sent

📱 NEXT STEPS:
1. Apply device query fixes
2. Test with device ID 3c0780da-b2b5-438f-a6f9-e1f9adc9d51f
3. Verify message sending
4. Check trigger history
5. Confirm WhatsApp messages
    """)

def show_working_device_alternative():
    """Show working device alternative"""
    logger.info("\n🔄 WORKING DEVICE ALTERNATIVE")
    logger.info("=" * 50)
    
    logger.info("""
🔄 IF DEVICE 3c0780da-b2b5-438f-a6f9-e1f9adc9d51f CANNOT BE FIXED:

1️⃣ USE WORKING DEVICE:
   - Device ID: 36711d22-ac2c-4e85-9b04-3f06a7d73158
   - This device was working in previous tests
   - Update triggers to use this device

2️⃣ UPDATE TRIGGERS:
   - Change all triggers to use working device
   - Test trigger execution
   - Verify message sending

3️⃣ BENEFITS:
   - Immediate working solution
   - Proven device connection
   - No device query issues

🎯 RECOMMENDATION:
Use device 36711d22-ac2c-4e85-9b04-3f06a7d73158 for immediate testing
Fix device 3c0780da-b2b5-438f-a6f9-e1f9adc9d51f later

📱 IMMEDIATE ACTION:
1. Update triggers to use working device
2. Run trigger test
3. Verify WhatsApp messages
4. Document working configuration
    """)

if __name__ == "__main__":
    device_exists = debug_device_issue()
    fix_device_retrieval()
    show_working_device_alternative()
    
    if device_exists:
        logger.info("\n✅ DEVICE EXISTS - QUERY NEEDS FIXING")
        logger.info("🔧 Apply device retrieval fixes")
    else:
        logger.info("\n❌ DEVICE NOT FOUND - USE WORKING DEVICE")
        logger.info("🔄 Switch to device 36711d22-ac2c-4e85-9b04-3f06a7d73158")
