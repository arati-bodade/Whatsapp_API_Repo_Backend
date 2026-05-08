#!/usr/bin/env python3
"""
Debug current trigger execution and message sending
"""

import logging
import asyncio
from datetime import datetime
from db.session import SessionLocal
from models.google_sheet import GoogleSheet, GoogleSheetTrigger, GoogleSheetTriggerHistory
from services.google_sheets_automation import GoogleSheetsAutomationService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_current_execution():
    """Debug current trigger execution status"""
    logger.info("🔍 DEBUGGING CURRENT TRIGGER EXECUTION")
    logger.info("=" * 60)
    
    db = SessionLocal()
    try:
        # 1. Check recent trigger history
        logger.info("📋 CHECKING RECENT TRIGGER HISTORY")
        
        recent_history = db.query(GoogleSheetTriggerHistory).order_by(
            GoogleSheetTriggerHistory.triggered_at.desc()
        ).limit(10).all()
        
        logger.info(f"📊 Found {len(recent_history)} recent history records")
        
        if not recent_history:
            logger.warning("⚠️ No trigger history found - triggers may not be executing")
        else:
            for item in recent_history:
                logger.info(f"📅 {item.triggered_at}: {item.status}")
                logger.info(f"   Phone: {item.phone_number}")
                logger.info(f"   Message: {item.message_content[:50]}...")
                if item.error_message:
                    logger.info(f"   ❌ Error: {item.error_message}")
        
        # 2. Check active triggers and their configuration
        logger.info("\n⚡ CHECKING ACTIVE TRIGGERS")
        
        active_triggers = db.query(GoogleSheetTrigger).filter(
            GoogleSheetTrigger.is_enabled == True
        ).all()
        
        logger.info(f"📊 Found {len(active_triggers)} active triggers")
        
        for trigger in active_triggers:
            logger.info(f"⚡ Trigger: {trigger.trigger_id}")
            logger.info(f"   Type: {trigger.trigger_type}")
            logger.info(f"   Device: {trigger.device_id}")
            logger.info(f"   Status Column: {trigger.status_column}")
            logger.info(f"   Trigger Value: {trigger.trigger_value}")
            logger.info(f"   Message: {trigger.message_template}")
            logger.info(f"   Config: {trigger.trigger_config}")
            logger.info(f"   Last Triggered: {trigger.last_triggered_at}")
        
        # 3. Check Google Sheet data
        logger.info("\n📊 CHECKING GOOGLE SHEET DATA")
        
        if active_triggers:
            sheet = db.query(GoogleSheet).filter(
                GoogleSheet.id == active_triggers[0].sheet_id
            ).first()
            
            if sheet:
                logger.info(f"📊 Sheet: {sheet.sheet_name} ({sheet.spreadsheet_id})")
                
                automation_service = GoogleSheetsAutomationService(db)
                
                try:
                    data, headers = automation_service.sheets_service.get_sheet_data_with_headers(
                        sheet.spreadsheet_id, "Sheet1"
                    )
                    logger.info(f"📊 Found {len(data)} rows with headers: {headers}")
                    
                    # Show first few rows
                    for i, row in enumerate(data[:5]):
                        logger.info(f"   Row {i+1}: {row}")
                    
                    # Check for matching status values
                    status_values = set()
                    for row in data:
                        for key, value in row.items():
                            if key and value:
                                status_values.add(str(value).strip().upper())
                    
                    logger.info(f"📊 Status values found in sheet: {list(status_values)}")
                    
                    # Check if expected trigger values exist
                    expected_values = ["SEND", "Send", "SENT"]
                    found_matches = status_values.intersection(set([v.upper() for v in expected_values]))
                    logger.info(f"📊 Matching status values: {list(found_matches)}")
                    
                    if not found_matches:
                        logger.warning("⚠️ No matching status values found! Triggers won't execute.")
                        logger.info("🔧 SOLUTION: Add Status column with 'Send' values to your Google Sheet")
                    
                except Exception as e:
                    logger.error(f"❌ Error getting sheet data: {e}")
        
        # 4. Test manual trigger execution
        logger.info("\n🧪 TESTING MANUAL TRIGGER EXECUTION")
        
        automation_service = GoogleSheetsAutomationService(db)
        
        try:
            logger.info("🔄 Running manual trigger execution...")
            result = asyncio.run(automation_service.process_all_active_triggers())
            logger.info(f"✅ Manual execution result: {result}")
            
            # Check if any new history was created
            new_history = db.query(GoogleSheetTriggerHistory).filter(
                GoogleSheetTriggerHistory.triggered_at >= datetime.now().replace(second=0, microsecond=0)
            ).all()
            
            if new_history:
                logger.info(f"📊 {len(new_history)} new history records created during test")
                for item in new_history:
                    logger.info(f"   📅 {item.triggered_at}: {item.status} - {item.phone_number}")
            else:
                logger.warning("⚠️ No new history records created during test")
            
        except Exception as e:
            logger.error(f"❌ Error during manual execution: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Debug error: {e}")
        return False
    finally:
        db.close()

def show_diagnostic_summary():
    """Show diagnostic summary"""
    logger.info("\n📋 DIAGNOSTIC SUMMARY")
    logger.info("=" * 50)
    
    logger.info("""
🔍 BASED ON YOUR LOGS:

✅ POSITIVE INDICATORS:
- Trigger history API working (200 OK responses)
- Background task is running
- Google Sheet is accessible
- Triggers are configured with device_id

❌ POSSIBLE ISSUES:
1. NO STATUS COLUMN:
   - Your Google Sheet has: Phone, Name, Time, Massage
   - Triggers expect: Status column with "Send" value
   - No matching rows found for execution

2. NO TRIGGER EXECUTION:
   - No new history records being created
   - Triggers not finding matching conditions
   - Messages not being sent

🔧 IMMEDIATE FIXES:

1. ADD STATUS COLUMN:
   - Open your Google Sheet
   - Add "Status" column (column E)
   - Set Status = "Send" for rows to trigger

2. OR UPDATE TRIGGER CONFIG:
   - Change status_column to existing column like "Name"
   - Change trigger_value to existing value like "jaypal"

3. OR USE NEW_ROW TRIGGERS:
   - Change trigger_type to "new_row"
   - No status matching needed
   - Triggers on new row addition

🔍 EXPECTED AFTER FIX:
- Background task finds matching rows
- Messages sent via WhatsApp device
- New history records created
- WhatsApp messages received

📱 CHECKLIST:
✅ Status column added to Google Sheet
✅ Status values set to "Send"
✅ Background task running
✅ Device connected
✅ Phone numbers formatted correctly
✅ Messages sent to WhatsApp
✅ Trigger history populated

🚀 NEXT STEPS:
1. Add Status column to Google Sheet
2. Set Status = "Send" for test rows
3. Monitor server logs for execution
4. Check WhatsApp for messages
5. Verify trigger history API
    """)

if __name__ == "__main__":
    success = debug_current_execution()
    show_diagnostic_summary()
    
    if success:
        logger.info("\n🎉 DEBUG COMPLETE!")
        logger.info("🔧 Follow the diagnostic summary above")
    else:
        logger.info("\n❌ DEBUG FAILED")
        logger.info("🔧 Check the errors above")
