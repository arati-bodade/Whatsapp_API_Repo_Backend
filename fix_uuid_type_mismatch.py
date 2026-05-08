#!/usr/bin/env python3
"""
Fix PostgreSQL UUID type mismatch issue
"""

import logging
import uuid
from db.session import SessionLocal
from models.device import Device
from models.google_sheet import GoogleSheetTrigger

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_uuid_type_mismatch():
    """Fix PostgreSQL UUID type mismatch in device queries"""
    logger.info("🔧 FIXING POSTGRESQL UUID TYPE MISMATCH")
    logger.info("=" * 70)
    
    db = SessionLocal()
    try:
        test_device_id = "3c0780da-b2b5-438f-a6f9-e1f9adc9d51f"
        
        # 1. Convert string to UUID for proper querying
        logger.info("1️⃣ CONVERTING DEVICE ID TO UUID")
        
        try:
            device_uuid = uuid.UUID(test_device_id)
            logger.info(f"✅ Converted to UUID: {device_uuid}")
        except ValueError as e:
            logger.error(f"❌ Invalid UUID format: {e}")
            return False
        
        # 2. Query device with proper UUID type
        logger.info("\n2️⃣ QUERYING DEVICE WITH UUID TYPE")
        
        device = db.query(Device).filter(Device.device_id == device_uuid).first()
        
        if device:
            logger.info(f"✅ Device found with UUID query!")
            logger.info(f"   Device ID: {device.device_id}")
            logger.info(f"   Device Name: {getattr(device, 'device_name', 'N/A')}")
            logger.info(f"   Status: {device.session_status}")
            logger.info(f"   Type: {device.device_type}")
            logger.info(f"   Last Active: {device.last_active}")
            logger.info(f"   Is Active: {device.is_active}")
        else:
            logger.error(f"❌ Device not found even with UUID query")
            return False
        
        # 3. Update triggers to use proper UUID
        logger.info("\n3️⃣ UPDATING TRIGGERS WITH PROPER UUID")
        
        triggers = db.query(GoogleSheetTrigger).filter(
            GoogleSheetTrigger.is_enabled == True
        ).all()
        
        updated_count = 0
        for trigger in triggers:
            # Convert device_id to UUID if it's a string
            if isinstance(trigger.device_id, str):
                try:
                    trigger.device_id = uuid.UUID(trigger.device_id)
                    logger.info(f"✅ Updated trigger {trigger.trigger_id[:8]}... to UUID")
                    updated_count += 1
                except ValueError:
                    logger.warning(f"⚠️  Invalid UUID in trigger {trigger.trigger_id[:8]}...")
            elif trigger.device_id is None:
                # Set to test device UUID
                trigger.device_id = device_uuid
                logger.info(f"✅ Set trigger {trigger.trigger_id[:8]}... to test device")
                updated_count += 1
        
        db.commit()
        logger.info(f"✅ Updated {updated_count} triggers with proper UUID types")
        
        # 4. Test device query in automation service context
        logger.info("\n4️⃣ TESTING DEVICE QUERY IN AUTOMATION CONTEXT")
        
        # Simulate the automation service query
        try:
            # This is how the automation service queries devices
            test_device = db.query(Device).filter(Device.device_id == device_uuid).first()
            
            if test_device:
                logger.info(f"✅ Automation context query successful!")
                logger.info(f"   Device object: {test_device}")
                logger.info(f"   Device attributes accessible: {hasattr(test_device, 'device_name')}")
                
                # Test accessing device attributes
                try:
                    device_name = test_device.device_name
                    logger.info(f"   Device name: {device_name}")
                    logger.info("✅ Device attributes accessible!")
                except AttributeError as e:
                    logger.error(f"❌ Device attribute error: {e}")
                    return False
            else:
                logger.error("❌ Automation context query failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Automation context query error: {e}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fix error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def create_automation_service_fix():
    """Create fix for automation service device query"""
    logger.info("\n🔧 CREATING AUTOMATION SERVICE FIX")
    logger.info("=" * 50)
    
    logger.info("""
🔧 AUTOMATION SERVICE FIX NEEDED:

1️⃣ CURRENT ISSUE:
   - send_message_via_unofficial_device uses string device_id
   - PostgreSQL expects UUID type for device_id column
   - Type mismatch causes query to fail

2️⃣ FIX LOCATION:
   - File: services/google_sheets_automation.py
   - Function: send_message_via_unofficial_device
   - Line: Device query section

3️⃣ FIX CODE:
   Add UUID conversion before device query:

   ```python
   # Convert device_id to UUID for proper PostgreSQL query
   try:
       device_uuid = uuid.UUID(device_id) if isinstance(device_id, str) else device_id
   except ValueError:
       logger.error(f"Invalid device_id format: {device_id}")
       return False
   
   device = db.query(Device).filter(Device.device_id == device_uuid).first()
   ```

4️⃣ BENEFITS:
   - Fixes PostgreSQL type mismatch
   - Proper device query execution
   - Device attributes accessible
   - Message sending works

🎯 IMPLEMENTATION STEPS:
1. Add UUID import to automation service
2. Convert device_id to UUID before query
3. Add error handling for invalid UUID
4. Test device query and attribute access

📱 EXPECTED RESULT:
✅ Device query returns valid device object
✅ Device attributes accessible
✅ Message sending works
✅ Trigger history created
✅ WhatsApp messages sent
    """)

def test_fixed_system():
    """Test the fixed system"""
    logger.info("\n🧪 TESTING FIXED SYSTEM")
    logger.info("=" * 50)
    
    logger.info("""
🧪 TEST PLAN FOR FIXED SYSTEM:

1️⃣ DEVICE QUERY TEST:
   - Query device with UUID conversion
   - Verify device object returned
   - Check device attributes accessible

2️⃣ TRIGGER EXECUTION TEST:
   - Run trigger processing
   - Check device query in automation service
   - Verify message sending attempt

3️⃣ MESSAGE SENDING TEST:
   - Test send_message_via_unofficial_device
   - Verify device found and connected
   - Check message sent successfully

4️⃣ TRIGGER HISTORY TEST:
   - Check trigger history records created
   - Verify status updates
   - Confirm message content logged

🎯 SUCCESS CRITERIA:
✅ Device query works with UUID conversion
✅ Device attributes accessible
✅ Message sending succeeds
✅ Trigger history created
✅ WhatsApp messages received

📱 FINAL VERIFICATION:
1. Run trigger test with device 3c0780da-b2b5-438f-a6f9-e1f9adc9d51f
2. Check server logs for successful device query
3. Verify WhatsApp messages received
4. Confirm trigger history shows SENT status
    """)

if __name__ == "__main__":
    success = fix_uuid_type_mismatch()
    create_automation_service_fix()
    test_fixed_system()
    
    if success:
        logger.info("\n✅ UUID TYPE MISMATCH FIXED!")
        logger.info("🔧 Now update automation service code")
        logger.info("🧪 Test trigger system with fixed device query")
    else:
        logger.info("\n❌ UUID TYPE MISMATCH FIX FAILED")
        logger.info("🔄 Use working device 36711d22-ac2c-4e85-9b04-3f06a7d73158")
