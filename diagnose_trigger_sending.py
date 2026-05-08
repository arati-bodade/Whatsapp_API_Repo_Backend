#!/usr/bin/env python3
"""
Diagnose trigger message sending issues
"""

import logging
import asyncio
from datetime import datetime
from db.session import SessionLocal
from models.google_sheet import GoogleSheet, GoogleSheetTrigger, TriggerType
from models.device import Device
from services.google_sheets_automation import GoogleSheetsAutomationService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def diagnose_trigger_sending():
    """Diagnose why triggers aren't sending messages"""
    logger.info("🔧 DIAGNOSING TRIGGER MESSAGE SENDING ISSUES")
    logger.info("=" * 60)
    
    db = SessionLocal()
    try:
        # 1. Check active triggers
        logger.info("🔍 CHECKING ACTIVE TRIGGERS")
        active_triggers = db.query(GoogleSheetTrigger).filter(
            GoogleSheetTrigger.is_enabled == True
        ).all()
        
        logger.info(f"📊 Found {len(active_triggers)} active triggers")
        
        for trigger in active_triggers:
            logger.info(f"⚡ Trigger: {trigger.trigger_id}")
            logger.info(f"   Type: {trigger.trigger_type}")
            logger.info(f"   Device: {trigger.device_id}")
            logger.info(f"   Message: {trigger.message_template}")
            logger.info(f"   Phone column: {trigger.phone_column}")
            logger.info(f"   Status column: {trigger.status_column}")
            logger.info(f"   Trigger value: {trigger.trigger_value}")
            logger.info(f"   Config: {trigger.trigger_config}")
            logger.info(f"   Last triggered: {trigger.last_triggered_at}")
        
        # 2. Check connected devices
        logger.info("\n📱 CHECKING CONNECTED DEVICES")
        connected_devices = db.query(Device).filter(
            Device.session_status == "connected"
        ).all()
        
        logger.info(f"📊 Found {len(connected_devices)} connected devices")
        
        for device in connected_devices:
            logger.info(f"📱 Device: {device.device_id}")
            logger.info(f"   Name: {device.device_name}")
            logger.info(f"   Status: {device.session_status}")
            logger.info(f"   Phone: {device.device_phone}")
        
        # 3. Check triggers with device_id
        logger.info("\n🔍 CHECKING TRIGGERS WITH DEVICE_ID")
        triggers_with_device = db.query(GoogleSheetTrigger).filter(
            GoogleSheetTrigger.is_enabled == True,
            GoogleSheetTrigger.device_id.isnot(None)
        ).all()
        
        logger.info(f"📊 Found {len(triggers_with_device)} triggers with device_id")
        
        for trigger in triggers_with_device:
            device = db.query(Device).filter(
                Device.device_id == trigger.device_id
            ).first()
            
            if device:
                logger.info(f"✅ Trigger {trigger.trigger_id} has connected device {device.device_name}")
            else:
                logger.info(f"❌ Trigger {trigger.trigger_id} has device_id {trigger.device_id} but device not found")
        
        # 4. Test manual trigger execution
        logger.info("\n🧪 TESTING MANUAL TRIGGER EXECUTION")
        automation_service = GoogleSheetsAutomationService(db)
        
        # Test with a specific trigger
        if triggers_with_device:
            test_trigger = triggers_with_device[0]
            logger.info(f"🧪 Testing trigger: {test_trigger.trigger_id}")
            
            # Get sheet data
            sheet = db.query(GoogleSheet).filter(
                GoogleSheet.id == test_trigger.sheet_id
            ).first()
            
            if sheet:
                logger.info(f"📊 Testing with sheet: {sheet.sheet_name}")
                
                # Get sheet data
                try:
                    data = automation_service.sheets_service.get_sheet_data(sheet.spreadsheet_id, "Sheet1!A:Z")
                    logger.info(f"📊 Found {len(data)} rows in sheet")
                    
                    # Show first few rows
                    for i, row in enumerate(data[:3]):
                        logger.info(f"   Row {i+1}: {row}")
                    
                    # Test trigger processing
                    logger.info("🧪 Processing trigger manually...")
                    result = asyncio.run(automation_service.process_all_active_triggers())
                    logger.info(f"🧪 Manual execution result: {result}")
                    
                except Exception as e:
                    logger.error(f"❌ Error during manual test: {e}")
            else:
                logger.error(f"❌ Sheet not found for trigger {test_trigger.trigger_id}")
        else:
            logger.warning("⚠️ No triggers with device_id found for testing")
        
        # 5. Check trigger history
        logger.info("\n📋 CHECKING TRIGGER HISTORY")
        from models.google_sheet import GoogleSheetTriggerHistory
        
        recent_history = db.query(GoogleSheetTriggerHistory).order_by(
            GoogleSheetTriggerHistory.triggered_at.desc()
        ).limit(10).all()
        
        logger.info(f"📊 Found {len(recent_history)} recent history records")
        
        for item in recent_history:
            logger.info(f"📅 {item.triggered_at}: {item.status} - {item.phone_number}")
            logger.info(f"   Message: {item.message_content[:50]}...")
            if item.error_message:
                logger.info(f"   Error: {item.error_message}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Diagnostic error: {e}")
        return False
    finally:
        db.close()

def show_fix_recommendations():
    """Show fix recommendations"""
    logger.info("\n🔧 FIX RECOMMENDATIONS")
    logger.info("=" * 50)
    
    logger.info("""
🔍 COMMON ISSUES AND FIXES:

1️⃣ NO CONNECTED DEVICES:
   - Check if WhatsApp devices are connected
   - Verify device session_status = "connected"
   - Reconnect devices if needed

2️⃣ TRIGGER MISSING DEVICE_ID:
   - Add device_id to trigger configuration
   - Use valid connected device ID
   - Example: "ee68cf44-168c-42b0-bf69-bff71cc7110b"

3️⃣ INCORRECT TRIGGER CONFIG:
   - Verify trigger_type = "time"
   - Check phone_column and status_column names
   - Ensure trigger_value matches sheet data

4️⃣ SHEET DATA ISSUES:
   - Verify phone numbers in correct format
   - Check status column values
   - Ensure time column has proper format

5️⃣ MESSAGE TEMPLATE MISSING:
   - Add message_template to trigger
   - Use placeholders like {{Name}}, {{Phone}}
   - Ensure template is not empty

🔧 QUICK FIXES:

1. UPDATE TRIGGER WITH DEVICE_ID:
   UPDATE google_sheet_triggers 
   SET device_id = 'ee68cf44-168c-42b0-bf69-bff71cc7110b'
   WHERE trigger_id = 'your-trigger-id';

2. ADD MESSAGE TEMPLATE:
   UPDATE google_sheet_triggers 
   SET message_template = 'Hello {{Name}}! Your message at {{Time}}'
   WHERE trigger_id = 'your-trigger-id';

3. VERIFY DEVICE CONNECTION:
   SELECT * FROM devices WHERE session_status = 'connected';

4. CHECK SHEET DATA:
   Make sure your Google Sheet has:
   - Phone column with numbers like: 9145291501
   - Status column with values like: Send
   - Time column with times like: 03.15 PM

🧪 TEST TRIGGER MANUALLY:
1. Add test data to Google Sheet
2. Create trigger with device_id
3. Run manual execution
4. Check logs for errors
5. Verify WhatsApp message received

🔍 EXPECTED LOGS:
- "📱 Using unofficial device {device_id} for message sending"
- "📱 Sending message via unofficial device {device_id} to {phone}"
- "✅ Message sent successfully via unofficial device"

❌ If you see these errors:
- "Device not found or not connected" → Fix device connection
- "Trigger missing message_template" → Add message template
- "No phone number found" → Check phone column
- "Invalid phone number format" → Check phone format

✅ SUCCESS INDICATORS:
- Device found and connected
- Phone number formatted correctly
- Message template personalized
- WhatsApp message sent
- Trigger history updated to SENT
    """)

if __name__ == "__main__":
    success = diagnose_trigger_sending()
    show_fix_recommendations()
    
    if success:
        logger.info("\n🎉 DIAGNOSTIC COMPLETE!")
        logger.info("🔧 Follow the fix recommendations above")
    else:
        logger.info("\n❌ DIAGNOSTIC FAILED")
        logger.info("🔧 Check the errors above")
