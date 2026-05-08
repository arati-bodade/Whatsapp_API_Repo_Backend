#!/usr/bin/env python3
"""
Fix trigger message sending issues
"""

import logging
from db.session import SessionLocal
from models.google_sheet import GoogleSheetTrigger

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_triggers():
    """Fix triggers to send messages properly"""
    logger.info("🔧 FIXING TRIGGER MESSAGE SENDING")
    logger.info("=" * 50)
    
    db = SessionLocal()
    try:
        # 1. Fix time triggers - add device_id and proper trigger_value
        logger.info("🔧 FIXING TIME TRIGGERS")
        
        time_triggers = db.query(GoogleSheetTrigger).filter(
            GoogleSheetTrigger.trigger_type == "time",
            GoogleSheetTrigger.is_enabled == True
        ).all()
        
        for trigger in time_triggers:
            if not trigger.device_id:
                logger.info(f"🔧 Adding device_id to trigger {trigger.trigger_id}")
                trigger.device_id = "ee68cf44-168c-42b0-bf69-bff71cc7110b"
            
            if not trigger.trigger_value or trigger.trigger_value.strip() == "":
                logger.info(f"🔧 Adding trigger_value 'Send' to trigger {trigger.trigger_id}")
                trigger.trigger_value = "Send"
            
            if not trigger.message_template or trigger.message_template.strip() == "":
                logger.info(f"🔧 Adding message template to trigger {trigger.trigger_id}")
                trigger.message_template = "Hello {{Name}}! This is your scheduled message at {{Time}}."
            
            if not trigger.trigger_config:
                logger.info(f"🔧 Adding trigger_config to trigger {trigger.trigger_id}")
                trigger.trigger_config = {
                    "specific_times": ["03.15 PM", "03.16 PM", "03.18 PM", "03.20 PM", "03.25 PM", "03.30 PM"],
                    "schedule_column": "Time"
                }
        
        # 2. Fix other triggers - add device_id
        logger.info("\n🔧 FIXING OTHER TRIGGERS")
        
        other_triggers = db.query(GoogleSheetTrigger).filter(
            GoogleSheetTrigger.trigger_type != "time",
            GoogleSheetTrigger.is_enabled == True,
            GoogleSheetTrigger.device_id.is_(None)
        ).all()
        
        for trigger in other_triggers:
            logger.info(f"🔧 Adding device_id to trigger {trigger.trigger_id}")
            trigger.device_id = "ee68cf44-168c-42b0-bf69-bff71cc7110b"
            
            if not trigger.message_template or trigger.message_template.strip() == "":
                logger.info(f"🔧 Adding message template to trigger {trigger.trigger_id}")
                trigger.message_template = "Hello {{Name}}! Your message has been triggered."
        
        db.commit()
        logger.info("✅ All triggers fixed successfully!")
        
        # 3. Show updated triggers
        logger.info("\n📋 UPDATED TRIGGERS:")
        
        updated_triggers = db.query(GoogleSheetTrigger).filter(
            GoogleSheetTrigger.is_enabled == True
        ).all()
        
        for trigger in updated_triggers:
            logger.info(f"⚡ {trigger.trigger_id}:")
            logger.info(f"   Type: {trigger.trigger_type}")
            logger.info(f"   Device: {trigger.device_id}")
            logger.info(f"   Message: {trigger.message_template}")
            logger.info(f"   Trigger Value: {trigger.trigger_value}")
            logger.info(f"   Config: {trigger.trigger_config}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error fixing triggers: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def show_test_instructions():
    """Show test instructions"""
    logger.info("\n🧪 TEST INSTRUCTIONS")
    logger.info("=" * 50)
    
    logger.info("""
📋 GOOGLE SHEET SETUP:

Add this data to your Google Sheet:

| Phone      | Name    | Time     | Status | Message        |
|------------|---------|----------|--------|----------------|
| 9145291501 | jaypal  | 03.15 PM | Send   | Test message   |
| 7507640770 | vikas   | 03.16 PM | Send   | Test message   |
| 9763615655 | vikas_two | 03.18 PM | Send   | Test message   |
| 7887640770 | new     | 03.20 PM | Send   | Test message   |

🧪 TESTING STEPS:

1. ADD TEST DATA:
   - Add the rows above to your Google Sheet
   - Make sure column names match exactly

2. TRIGGER EXECUTION:
   - Triggers will run automatically every 30 seconds
   - Or run manual test: python -c "
     import asyncio
     from services.google_sheets_automation import GoogleSheetsAutomationService
     from db.session import SessionLocal
     db = SessionLocal()
     service = GoogleSheetsAutomationService(db)
     asyncio.run(service.process_all_active_triggers())
     "

3. MONITOR LOGS:
   - Watch for: "📱 Using unofficial device"
   - Watch for: "📱 Sending message via unofficial device"
   - Watch for: "✅ Message sent successfully"

4. CHECK WHATSAPP:
   - Messages should appear on your device
   - Check for test messages from the system

5. VERIFY TRIGGER HISTORY:
   - Check API: GET /api/google-sheets/triggers/history
   - Should show SENT status for successful messages

🔍 EXPECTED LOGS:
📱 Raw phone from sheet: 9145291501
📱 Formatted phone: +919145291501
📱 Using unofficial device ee68cf44-168c-42b0-bf69-bff71cc7110b
📱 Personalized message: Hello jaypal! This is your scheduled message at 03.15 PM.
📤 Processing row 1 via unofficial device
📱 Sending message via unofficial device ee68cf44-168c-42b0-bf69-bff71cc7110b to +919145291501
✅ Message sent successfully via unofficial device to +919145291501

✅ SUCCESS INDICATORS:
- Device found and connected
- Phone number formatted correctly
- Message template personalized with row data
- WhatsApp message sent successfully
- Trigger history updated to SENT
- Sheet status updated to SENT

❌ IF STILL NOT WORKING:
1. Check device connection in frontend
2. Verify Google Sheet data exactly matches
3. Check server logs for errors
4. Test with a simple trigger first
5. Verify JWT token is not expired
    """)

if __name__ == "__main__":
    success = fix_triggers()
    show_test_instructions()
    
    if success:
        logger.info("\n🎉 TRIGGERS FIXED!")
        logger.info("🧪 Follow the test instructions above")
        logger.info("📱 Your triggers should now send messages properly")
    else:
        logger.info("\n❌ FIX FAILED")
        logger.info("🔧 Check the errors above")
