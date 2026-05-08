#!/usr/bin/env python3
"""
Debug trigger history issues
"""

import logging
from datetime import datetime
from db.session import SessionLocal
from models.google_sheet import GoogleSheetTriggerHistory, GoogleSheet

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_trigger_history():
    """Debug trigger history issues"""
    logger.info("🔍 DEBUGGING TRIGGER HISTORY")
    logger.info("=" * 50)
    
    db = SessionLocal()
    try:
        # Check if trigger history table exists
        try:
            db.execute("SELECT 1 FROM google_sheet_trigger_history LIMIT 1")
            logger.info("✅ google_sheet_trigger_history table exists")
        except Exception as e:
            logger.error(f"❌ google_sheet_trigger_history table doesn't exist: {e}")
            return False
        
        # Count total history records
        total_history = db.query(GoogleSheetTriggerHistory).count()
        logger.info(f"📊 Total trigger history records: {total_history}")
        
        # Get recent history
        recent_history = db.query(GoogleSheetTriggerHistory).order_by(
            GoogleSheetTriggerHistory.triggered_at.desc()
        ).limit(5).all()
        
        logger.info(f"📋 Recent history ({len(recent_history)} records):")
        for item in recent_history:
            logger.info(f"   📅 {item.triggered_at}: {item.status} - {item.phone_number}")
            logger.info(f"      Message: {item.message_content[:50]}...")
            logger.info(f"      Sheet: {item.sheet_id}")
        
        # Check sheets
        sheets = db.query(GoogleSheet).all()
        logger.info(f"📋 Available sheets: {len(sheets)}")
        for sheet in sheets:
            logger.info(f"   📊 {sheet.id}: {sheet.sheet_name}")
        
        # Check if triggers are enabled
        from models.google_sheet import GoogleSheetTrigger, TriggerType
        active_triggers = db.query(GoogleSheetTrigger).filter(
            GoogleSheetTrigger.is_enabled == True
        ).all()
        
        logger.info(f"🔧 Active triggers: {len(active_triggers)}")
        for trigger in active_triggers:
            logger.info(f"   ⚡ {trigger.trigger_id}: {trigger.trigger_type}")
            logger.info(f"      Device: {trigger.device_id}")
            logger.info(f"      Last triggered: {trigger.last_triggered_at}")
            logger.info(f"      Message: {trigger.message_template}")
        
        # Test trigger execution manually
        logger.info("\n🧪 TESTING TRIGGER EXECUTION")
        from services.google_sheets_automation import GoogleSheetsAutomationService
        
        automation_service = GoogleSheetsAutomationService(db)
        
        # Process time-based triggers
        logger.info("🕐 Processing time-based triggers...")
        import asyncio
        result = asyncio.run(automation_service.process_time_based_triggers())
        logger.info(f"   Result: {result}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error debugging trigger history: {e}")
        return False
    finally:
        db.close()

def show_troubleshooting_guide():
    """Show troubleshooting guide"""
    logger.info("\n🔧 TRIGGER HISTORY TROUBLESHOOTING GUIDE")
    logger.info("=" * 50)
    
    logger.info("""
🔍 ISSUE: Trigger history is empty and refresh button not working

📋 POSSIBLE CAUSES:

1️⃣ NO TRIGGER EXECUTION:
   - Time-based triggers haven't executed yet
   - Triggers are disabled
   - Background task not running
   - Timing conditions not met

2️⃣ DATABASE ISSUES:
   - Trigger history table doesn't exist
   - Database connection issues
   - Table permissions problems

3️⃣ FRONTEND ISSUES:
   - Refresh button JavaScript error
   - API endpoint not called correctly
   - Response not processed properly

🔧 SOLUTIONS:

1️⃣ CHECK TRIGGER EXECUTION:
   - Verify triggers are enabled (is_enabled = true)
   - Check timing conditions are met
   - Monitor server logs for execution
   - Run manual trigger test

2️⃣ VERIFY DATABASE:
   - Check google_sheet_trigger_history table exists
   - Verify database connection
   - Check table permissions

3️⃣ TEST API ENDPOINT:
   - Call /api/google-sheets/triggers/history directly
   - Check response format
   - Verify pagination parameters

4️⃣ DEBUG FRONTEND:
   - Check browser console for errors
   - Verify refresh button event handler
   - Check API call implementation

📋 API ENDPOINT TEST:
GET /api/google-sheets/triggers/history?page=1&per_page=50
Authorization: Bearer YOUR_JWT_TOKEN

Expected Response:
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "sheet_id": "uuid", 
      "sheet_name": "Sheet Name",
      "phone_number": "+1234567890",
      "message_content": "Hello!",
      "status": "SENT",
      "triggered_at": "2024-03-09T15:30:00",
      "error_message": null
    }
  ]
}

🧪 MANUAL TRIGGER TEST:
1. Create a test trigger with current time
2. Enable the trigger
3. Run background task manually
4. Check trigger history
5. Verify message received

🔍 DEBUGGING STEPS:

1. CHECK SERVER LOGS:
   - Look for "🕐 Processing time-based trigger"
   - Look for "🚀 Time trigger executing NOW"
   - Look for "📱 Using unofficial device"
   - Look for "✅ Message sent successfully"

2. VERIFY DATABASE:
   - SELECT COUNT(*) FROM google_sheet_trigger_history
   - SELECT * FROM google_sheet_trigger_history ORDER BY triggered_at DESC LIMIT 5

3. TEST API DIRECTLY:
   curl -X GET "http://localhost:8000/api/google-sheets/triggers/history" \
        -H "Authorization: Bearer YOUR_TOKEN"

4. CHECK FRONTEND:
   - Open browser developer tools
   - Click refresh button
   - Check Network tab for API call
   - Check Console for JavaScript errors

🚀 QUICK FIXES:

1. CREATE TEST TRIGGER:
{
  "trigger_type": "time",
  "is_enabled": true,
  "phone_column": "Phone",
  "status_column": "Time", 
  "trigger_value": "03.15 PM",
  "message_template": "Test message at {{Time}}",
  "device_id": "ee68cf44-168c-42b0-bf69-bff71cc7110b",
  "execution_interval": 60,  // Every minute for testing
  "trigger_config": {
    "specific_times": ["03.15 PM"]
  }
}

2. RUN MANUAL TEST:
   - Add test data to Google Sheet
   - Set current time in Time column
   - Trigger should execute within 30 seconds
   - Check history and WhatsApp

3. VERIFY BACKGROUND TASK:
   - Check if background task is running
   - Monitor server logs for activity
   - Restart server if needed

🎯 EXPECTED RESULTS:
- Trigger history should populate with execution records
- Refresh button should load new data
- Messages should be sent via unofficial device
- Server logs should show execution details
    """)

if __name__ == "__main__":
    success = debug_trigger_history()
    show_troubleshooting_guide()
    
    if success:
        logger.info("\n✅ DEBUGGING COMPLETE")
        logger.info("🔍 Check the results above to identify the issue")
    else:
        logger.info("\n❌ DEBUGGING FAILED")
        logger.info("🔧 Check database connection and table structure")
