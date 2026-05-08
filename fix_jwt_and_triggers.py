#!/usr/bin/env python3
"""
Fix JWT token issue and trigger message sending
"""

import logging
from datetime import datetime, timedelta
from db.session import SessionLocal
from models.google_sheet import GoogleSheetTrigger, TriggerType
from services.google_sheets_automation import GoogleSheetsAutomationService
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_jwt_and_trigger_issues():
    """Fix JWT token and trigger message sending issues"""
    logger.info("🔧 FIXING JWT TOKEN AND TRIGGER ISSUES")
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
            logger.info(f"   Last triggered: {trigger.last_triggered_at}")
            logger.info(f"   Config: {trigger.trigger_config}")
        
        # 2. Test time trigger execution manually
        logger.info("\n🧪 TESTING TIME TRIGGER EXECUTION")
        automation_service = GoogleSheetsAutomationService(db)
        
        # Process time-based triggers
        logger.info("🕐 Processing time-based triggers...")
        result = asyncio.run(automation_service.process_time_based_triggers())
        logger.info(f"   Result: {result}")
        
        # 3. Check trigger history
        logger.info("\n📋 CHECKING TRIGGER HISTORY")
        from models.google_sheet import GoogleSheetTriggerHistory
        
        history = db.query(GoogleSheetTriggerHistory).order_by(
            GoogleSheetTriggerHistory.triggered_at.desc()
        ).limit(10).all()
        
        logger.info(f"📊 Found {len(history)} recent history records")
        for item in history:
            logger.info(f"   📅 {item.triggered_at}: {item.status} - {item.phone_number}")
            logger.info(f"      Message: {item.message_content[:50]}...")
            logger.info(f"      Error: {item.error_message}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False
    finally:
        db.close()

def show_jwt_fix_guide():
    """Show JWT token fix guide"""
    logger.info("\n🔑 JWT TOKEN FIX GUIDE")
    logger.info("=" * 50)
    
    logger.info("""
🔍 ISSUE: JWT Token Expired (401 Unauthorized)

📋 ERROR DETAILS:
- API Error: 401 {}
- JWT Error: Token has expired
- GET /api/google-sheets/triggers/history HTTP/1.1 401 Unauthorized
- Frontend cannot authenticate with backend

🔧 SOLUTIONS:

1️⃣ REFRESH JWT TOKEN:
   - Log out and log back in to the application
   - This will generate a new JWT token
   - Old token will be invalidated
   - New token will have fresh expiration

2️⃣ CHECK TOKEN EXPIRY:
   - JWT tokens typically expire after 24 hours
   - Check token expiration time
   - Implement auto-refresh if needed

3️⃣ VERIFY AUTHENTICATION:
   - Ensure user is properly logged in
   - Check token is being sent in headers
   - Verify token format and content

📱 FRONTEND FIX:
1. Clear browser localStorage/sessionStorage
2. Log out from the application
3. Log back in with valid credentials
4. Refresh the trigger history page
5. Test the refresh button

🔧 BACKEND FIX:
1. Check JWT secret key configuration
2. Verify token expiration settings
3. Ensure proper token validation
4. Check user authentication flow

🚀 TRIGGER MESSAGE SENDING FIX:

🔍 ISSUE: Triggers created but messages not sent

📋 POSSIBLE CAUSES:
1. Timing conditions not met
2. Device connection issues
3. Background task not running
4. Trigger configuration errors
5. WhatsApp API issues

🔧 TROUBLESHOOTING STEPS:

1️⃣ CHECK TIMING:
   - Verify current time matches trigger times
   - Check timezone settings
   - Ensure specific_times are correct

2️⃣ VERIFY DEVICE CONNECTION:
   - Check device is connected
   - Verify device_id is correct
   - Test device manually

3️⃣ MONITOR BACKGROUND TASK:
   - Check if background task is running
   - Look for execution logs
   - Verify polling interval

4️⃣ TEST TRIGGER MANUALLY:
   - Create trigger with current time
   - Set execution_interval to 60 seconds
   - Monitor logs for execution

🧪 QUICK TEST:

Create a test trigger with these settings:
{
  "trigger_type": "time",
  "is_enabled": true,
  "phone_column": "Phone",
  "status_column": "Time",
  "trigger_value": "04.10 PM",
  "message_template": "Test message at {{Time}}",
  "device_id": "ee68cf44-168c-42b0-bf69-bff71cc7110b",
  "execution_interval": 60,  // Every minute
  "trigger_config": {
    "specific_times": ["04.10 PM", "04.11 PM", "04.12 PM"]
  }
}

📱 GOOGLE SHEET SETUP:
Add this row to your Google Sheet:
Phone: +919145291501
Name: Test User
Time: 04.10 PM
Status: Send
Message: Test message

🔍 MONITORING LOGS:
Watch for these log messages:
- "🕐 Processing time-based trigger {trigger_id}"
- "🚀 Time trigger {trigger_id} executing NOW"
- "📱 Using unofficial device {device_id} for message sending"
- "📱 Sending message via unofficial device {device_id} to {phone}"
- "✅ Message sent successfully via unofficial device to {phone}"

🎯 EXPECTED RESULTS:
- JWT token refreshed and working
- Trigger history API returning data
- Refresh button working properly
- Time triggers executing and sending messages
- Messages received on WhatsApp

📋 VERIFICATION CHECKLIST:
✅ Log out and log back in
✅ JWT token refreshed
✅ Trigger history API working
✅ Refresh button functional
✅ Time triggers executing
✅ Messages being sent
✅ WhatsApp messages received
    """)

if __name__ == "__main__":
    success = fix_jwt_and_trigger_issues()
    show_jwt_fix_guide()
    
    if success:
        logger.info("\n✅ DIAGNOSTIC COMPLETE")
        logger.info("🔑 Follow the JWT fix guide above")
        logger.info("🚀 Test trigger execution after JWT fix")
    else:
        logger.info("\n❌ DIAGNOSTIC FAILED")
        logger.info("🔧 Check backend logs and configuration")
