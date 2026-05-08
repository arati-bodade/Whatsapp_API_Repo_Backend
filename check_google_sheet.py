#!/usr/bin/env python3
"""
Check Google Sheet configuration and triggers
"""

import logging
import asyncio
from datetime import datetime
from db.session import SessionLocal

def get_default_sheet_id():
    """Get default active sheet ID dynamically"""
    from db.session import SessionLocal
    from models.google_sheet import GoogleSheet, SheetStatus
    
    db = SessionLocal()
    try:
        sheet = db.query(GoogleSheet).filter(
            GoogleSheet.status == SheetStatus.ACTIVE
        ).first()
        return sheet.spreadsheet_id if sheet else "1eF28T3dsJ78IaDSVQI0T3wvCD9lQBkqHhzjgYE1mEjw"
    finally:
        db.close()

from models.google_sheet import GoogleSheet, GoogleSheetTrigger, TriggerType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_google_sheet():
    """Check the Google Sheet structure and triggers"""
    logger.info("🔍 CHECKING GOOGLE SHEET CONFIGURATION")
    logger.info("=" * 60)
    
    # Sheet ID from URL
    sheet_id = get_default_sheet_id()
    
    db = SessionLocal()
    try:
        # Check sheet in database
        sheet = db.query(GoogleSheet).filter(
            GoogleSheet.spreadsheet_id == sheet_id
        ).first()
        
        if not sheet:
            logger.error(f"❌ Sheet {sheet_id} not found in database")
            logger.info("💡 Sheet must be connected first via API")
            return False
        
        logger.info(f"✅ Found sheet: {sheet.sheet_name}")
        logger.info(f"   Status: {sheet.status}")
        logger.info(f"   User ID: {sheet.user_id}")
        logger.info(f"   Created: {sheet.created_at}")
        
        # Check all triggers for this sheet
        triggers = db.query(GoogleSheetTrigger).filter(
            GoogleSheetTrigger.sheet_id == sheet.id,
            GoogleSheetTrigger.is_enabled == True
        ).all()
        
        logger.info(f"📊 Total triggers: {len(triggers)}")
        
        # Analyze triggers by type
        time_triggers = [t for t in triggers if t.trigger_type == TriggerType.TIME]
        row_triggers = [t for t in triggers if t.trigger_type != TriggerType.TIME]
        
        logger.info(f"🕐 Time-based triggers: {len(time_triggers)}")
        logger.info(f"📝 Row-based triggers: {len(row_triggers)}")
        
        # Show trigger details
        for i, trigger in enumerate(triggers):
            logger.info(f"\n📋 Trigger {i+1}: {trigger.trigger_id}")
            logger.info(f"   Type: {trigger.trigger_type}")
            logger.info(f"   Enabled: {trigger.is_enabled}")
            logger.info(f"   Phone Column: {trigger.phone_column}")
            logger.info(f"   Status Column: {trigger.status_column}")
            logger.info(f"   Trigger Value: {trigger.trigger_value}")
            logger.info(f"   Message Template: {trigger.message_template}")
            logger.info(f"   Config: {trigger.trigger_config}")
            logger.info(f"   Last Triggered: {trigger.last_triggered_at}")
        
        # Check if ready for time triggers
        if time_triggers:
            logger.info("\n✅ TIME TRIGGER READY")
            logger.info("   - Time-based triggers are configured")
            logger.info("   - Logic is implemented")
            logger.info("   - Background task should execute them")
            
            # Test next execution timing
            for trigger in time_triggers:
                config = trigger.trigger_config or {}
                interval = config.get('interval', 3600)
                last_triggered = trigger.last_triggered_at
                
                if last_triggered:
                    from datetime import timedelta
                    next_run = last_triggered + timedelta(seconds=interval)
                    time_until = next_run - datetime.utcnow()
                    
                    if time_until.total_seconds() > 0:
                        hours = time_until.total_seconds() // 3600
                        minutes = (time_until.total_seconds() % 3600) // 60
                        logger.info(f"   ⏰ Next execution in: {hours}h {minutes}m")
                    else:
                        logger.info(f"   ⚡ Overdue! Should execute now")
        else:
            logger.info("\n⚠️ NO TIME TRIGGERS")
            logger.info("   - Need to create time-based triggers")
            logger.info("   - Use create_time_trigger.py script")
            logger.info("   - Or create via frontend/API")
        
        # Check sheet structure requirements
        logger.info(f"\n📋 SHEET STRUCTURE REQUIREMENTS:")
        logger.info(f"   Required columns: Phone, Status")
        logger.info(f"   Phone column should contain: Phone numbers to message")
        logger.info(f"   Status column should contain: 'Send' to trigger")
        logger.info(f"   Optional: ScheduleTime column for advanced scheduling")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error checking sheet: {e}")
        return False
    finally:
        db.close()

def show_troubleshooting():
    """Show troubleshooting steps"""
    logger.info("\n🔧 TROUBLESHOOTING GUIDE")
    logger.info("=" * 60)
    
    logger.info("""
🔍 IF TIME TRIGGERS ARE NOT WORKING:

1. CHECK SHEET STATUS:
   - Sheet must be ACTIVE in database
   - Sheet must be properly connected

2. CHECK TRIGGER CONFIGURATION:
   - trigger_type must be "time"
   - is_enabled must be true
   - execution_interval must be > 0 (seconds)
   - phone_column must match sheet header
   - status_column must match sheet header
   - trigger_value must match value in Status column

3. CHECK BACKGROUND TASK:
   - Background task must be running
   - Look for logs: "🔄 LEGACY PROCESSING: Processing triggers"
   - Should process time triggers every 30 seconds

4. CHECK SERVER LOGS:
   - Look for: "🕐 Processing time-based trigger {trigger_id}"
   - Look for: "🚀 Time trigger {trigger_id} executing NOW"
   - Look for errors in trigger processing

5. CHECK MESSAGE SENDING:
   - Verify Official WhatsApp API is working
   - Check trigger history for execution records
   - Verify WhatsApp message receipt

📱 COMMON ISSUES:
- Sheet not connected to database
- Time trigger has interval of 0 or None
- Status column doesn't exist in sheet
- Phone column doesn't exist in sheet
- Background task not running
- Network connectivity issues
- WhatsApp API configuration problems
    """)

if __name__ == "__main__":
    success = check_google_sheet()
    show_troubleshooting()
    
    if success:
        logger.info("\n✅ GOOGLE SHEET CHECK COMPLETED")
        logger.info("🚀 Ready for time-based trigger testing!")
    else:
        logger.info("\n❌ GOOGLE SHEET CHECK FAILED")
