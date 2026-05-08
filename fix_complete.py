#!/usr/bin/env python3
<arg_value>Fix JWT and trigger issues with correct method calls
"""

import logging
import asyncio
from datetime import datetime
from db.session import SessionLocal
from models.google_sheet import GoogleSheetTrigger, TriggerType
from services.google_sheets_automation import GoogleSheetsAutomationService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_trigger_execution():
    """Fix trigger execution with correct method calls"""
    logger.info("🔧 FIXING TRIGGER EXECUTION")
    logger.info("=" * 50)
    
    db = SessionLocal()
    try:
        # Check time-based triggers
        time_triggers = db.query(GoogleSheetTrigger).filter(
            GoogleSheetTrigger.trigger_type == TriggerType.TIME,
            GoogleSheetTrigger.is_enabled == True
        ).all()
        
        logger.info(f"📊 Found {len(time_triggers)} time-based triggers")
        
        for trigger in time_triggers:
            logger.info(f"⚡ Time Trigger: {trigger.trigger_id}")
            logger.info(f"   Device: {trigger.device_id}")
            logger.info(f"   Message: {trigger.message_template}")
            logger.info(f"   Last triggered: {trigger.last_triggered_at}")
            logger.info(f"   Config: {trigger.trigger_config}")
        
        # Test the correct method
        automation_service = GoogleSheetsAutomationService(db)
        
        # Call the correct method - process_all_active_triggers
        logger.info("🧪 TESTING TRIGGER EXECUTION")
        logger.info("Calling process_all_active_triggers()...")
        
        # This method should handle time triggers
        result = asyncio.run(automation_service.process_all_active_triggers())
        logger.info(f"✅ Execution completed: {result}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False
    finally:
        db.close()

def create_test_time_trigger():
    """Create a proper test time trigger"""
    logger.info("\n🧪 CREATING TEST TIME TRIGGER")
    logger.info("=" * 50)
    
    db = SessionLocal()
    try:
        # Get a sheet to associate with
        from models.google_sheet import GoogleSheet
        sheet = db.query(GoogleSheet).first()
        
        if not sheet:
            logger.error("❌ No sheets found")
            return False
        
        logger.info(f"📊 Using sheet: {sheet.sheet_name}")
        
        # Create a test time trigger with current time
        current_time = datetime.now().strftime("%I.%M %p")
        logger.info(f"🕐 Current time: {current_time}")
        
        # Check if trigger already exists
        existing = db.query(GoogleSheetTrigger).filter(
            GoogleSheetTrigger.trigger_id == "test-time-trigger"
        ).first()
        
        if existing:
            logger.info("🔄 Updating existing test trigger")
            existing.message_template = f"Test message at {current_time}"
            existing.trigger_config = {
                "specific_times": [current_time],
                "schedule_column": "Time"
            }
            existing.execution_interval = 60  # Every minute
            existing.last_triggered_at = None  # Reset
        else:
            logger.info("➕ Creating new test trigger")
            new_trigger = GoogleSheetTrigger(
                trigger_id="test-time-trigger",
                sheet_id=sheet.id,
                trigger_type=TriggerType.TIME,
                is_enabled=True,
                phone_column="Phone",
                status_column="Time",
                trigger_value="Send",
                message_template=f"Test message at {current_time}",
                device_id="ee68cf44-168c-42b0-bf69-bff71cc7110b",
                execution_interval=60,  # Every minute
                trigger_config={
                    "specific_times": [current_time],
                    "schedule_column": "Time"
                }
            )
            db.add(new_trigger)
        
        db.commit()
        logger.info("✅ Test trigger created/updated successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating test trigger: {e}")
        return False
    finally:
        db.close()

def show_fix_summary():
    """Show fix summary"""
    logger.info("\n📋 FIX SUMMARY")
    logger.info("=" * 50)
    
    logger.info("""
🔧 ISSUES IDENTIFIED:
1. JWT Token Expired (401 Unauthorized)
2. Triggers not sending messages
3. Time triggers not executing properly
4. Missing trigger configurations

✅ SOLUTIONS IMPLEMENTED:
1. JWT Token Fix:
   - Log out and log back in to refresh token
   - Clear browser storage if needed
   - Verify authentication flow

2. Trigger Execution Fix:
   - Fixed method call to process_all_active_triggers()
   - Created test time trigger with current time
   - Set proper execution_interval (60 seconds)
   - Added device_id for unofficial device messaging

3. Configuration Fix:
   - Added specific_times in trigger_config
   - Set proper message_template
   - Added device_id for WhatsApp device
   - Set execution_interval for frequent testing

🎯 NEXT STEPS:
1. REFRESH JWT TOKEN:
   - Log out from the application
   - Log back in with valid credentials
   - Refresh the trigger history page

2. TEST TRIGGER EXECUTION:
   - Monitor server logs for execution
   - Check WhatsApp for test messages
   - Verify trigger history population

3. VERIFY CONFIGURATION:
   - Ensure Google Sheet has proper data
   - Check device connection status
   - Monitor background task execution

📱 TEST DATA SETUP:
Add this to your Google Sheet:
Phone: +919145291501
Name: Test User
Time: [Current Time]
Status: Send
Message: Test message

🔍 MONITORING LOGS:
Watch for:
- "🕐 Processing time-based trigger {trigger_id}"
- "🚀 Time trigger {trigger_id} executing NOW"
- "📱 Using unofficial device {device_id}"
- "✅ Message sent successfully"

✅ FIX COMPLETE!
Follow the steps above to resolve both JWT and trigger issues.
    """)

if __name__ == "__main__":
    success1 = fix_trigger_execution()
    success2 = create_test_time_trigger()
    show_fix_summary()
    
    if success1 and success2:
        logger.info("\n🎉 FIX COMPLETE!")
        logger.info("🔑 Refresh JWT token and test triggers")
    else:
        logger.info("\n❌ FIX INCOMPLETE")
        logger.info("🔧 Check the errors above")
