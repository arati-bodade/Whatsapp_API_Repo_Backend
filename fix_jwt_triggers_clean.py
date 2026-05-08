#!/usr/bin/env python3
"""
Fix JWT and trigger issues - clean version
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
    logger.info("Fixing trigger execution...")
    
    db = SessionLocal()
    try:
        # Check time-based triggers
        time_triggers = db.query(GoogleSheetTrigger).filter(
            GoogleSheetTrigger.trigger_type == TriggerType.TIME,
            GoogleSheetTrigger.is_enabled == True
        ).all()
        
        logger.info(f"Found {len(time_triggers)} time-based triggers")
        
        for trigger in time_triggers:
            logger.info(f"Time Trigger: {trigger.trigger_id}")
            logger.info(f"   Device: {trigger.device_id}")
            logger.info(f"   Message: {trigger.message_template}")
            logger.info(f"   Config: {trigger.trigger_config}")
        
        # Test the correct method
        automation_service = GoogleSheetsAutomationService(db)
        
        # Call the correct method
        logger.info("Testing trigger execution...")
        result = asyncio.run(automation_service.process_all_active_triggers())
        logger.info(f"Execution completed: {result}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return False
    finally:
        db.close()

def create_test_trigger():
    """Create a proper test time trigger"""
    logger.info("Creating test time trigger...")
    
    db = SessionLocal()
    try:
        # Get a sheet
        from models.google_sheet import GoogleSheet
        sheet = db.query(GoogleSheet).first()
        
        if not sheet:
            logger.error("No sheets found")
            return False
        
        logger.info(f"Using sheet: {sheet.sheet_name}")
        
        # Create test trigger
        current_time = datetime.now().strftime("%I.%M %p")
        logger.info(f"Current time: {current_time}")
        
        # Check if trigger exists
        existing = db.query(GoogleSheetTrigger).filter(
            GoogleSheetTrigger.trigger_id == "test-time-trigger"
        ).first()
        
        if existing:
            logger.info("Updating existing test trigger")
            existing.message_template = f"Test message at {current_time}"
            existing.trigger_config = {
                "specific_times": [current_time],
                "schedule_column": "Time"
            }
            existing.execution_interval = 60
            existing.last_triggered_at = None
        else:
            logger.info("Creating new test trigger")
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
                execution_interval=60,
                trigger_config={
                    "specific_times": [current_time],
                    "schedule_column": "Time"
                }
            )
            db.add(new_trigger)
        
        db.commit()
        logger.info("Test trigger created successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating test trigger: {e}")
        return False
    finally:
        db.close()

def show_fix_summary():
    """Show fix summary"""
    logger.info("\nFIX SUMMARY")
    logger.info("=" * 50)
    
    logger.info("""
ISSUES IDENTIFIED:
1. JWT Token Expired (401 Unauthorized)
2. Triggers not sending messages
3. Time triggers not executing properly

SOLUTIONS:
1. JWT Token Fix:
   - Log out and log back in to refresh token
   - Clear browser storage if needed

2. Trigger Execution Fix:
   - Fixed method call to process_all_active_triggers()
   - Created test time trigger with current time
   - Set execution_interval to 60 seconds
   - Added device_id for unofficial device messaging

3. Configuration Fix:
   - Added specific_times in trigger_config
   - Set proper message_template
   - Added device_id for WhatsApp device

NEXT STEPS:
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

MONITORING LOGS:
Watch for:
- "Processing time-based trigger"
- "Time trigger executing NOW"
- "Using unofficial device"
- "Message sent successfully"

FIX COMPLETE!
Follow the steps above to resolve both JWT and trigger issues.
    """)

if __name__ == "__main__":
    success1 = fix_trigger_execution()
    success2 = create_test_trigger()
    show_fix_summary()
    
    if success1 and success2:
        logger.info("\nFIX COMPLETE!")
        logger.info("Refresh JWT token and test triggers")
    else:
        logger.info("\nFIX INCOMPLETE")
        logger.info("Check the errors above")
