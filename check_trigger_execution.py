#!/usr/bin/env python3
"""
Check why triggers aren't executing
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

from models.google_sheet import GoogleSheet, GoogleSheetTrigger
from services.google_sheets_automation import GoogleSheetsAutomationService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_trigger_execution():
    """Check why triggers aren't executing"""
    logger.info("🔍 CHECKING TRIGGER EXECUTION")
    logger.info("=" * 70)
    
    db = SessionLocal()
    try:
        # 1. Check if background task is running
        logger.info("1️⃣ CHECKING BACKGROUND TASK STATUS")
        logger.info("🔄 Looking for 'Processing all active triggers...' in logs")
        logger.info("🔍 If not seen, background task is not running")
        
        # 2. Run background task manually
        logger.info("\n2️⃣ RUNNING BACKGROUND TASK MANUALLY")
        
        automation_service = GoogleSheetsAutomationService(db)
        
        logger.info("🔄 Calling process_all_active_triggers()...")
        result = asyncio.run(automation_service.process_all_active_triggers())
        
        logger.info(f"🔄 Background task result: {result}")
        
        # 3. Check Google Sheet data
        logger.info("\n3️⃣ CHECKING GOOGLE SHEET DATA")
        
        sheet = db.query(GoogleSheet).filter(
            GoogleSheet.spreadsheet_id == get_default_sheet_id()
        ).first()
        
        if sheet:
            try:
                data, headers = automation_service.sheets_service.get_sheet_data_with_headers(
                    sheet.spreadsheet_id, "Sheet1"
                )
                
                logger.info(f"📊 Found {len(data)} rows with headers: {headers}")
                
                # Check for Status column
                if 'Status' not in headers:
                    logger.error("❌ Status column missing!")
                    return False
                
                # Check for Send values
                send_rows = []
                for i, row in enumerate(data):
                    if 'Status' in row and str(row['Status']).strip().upper() == 'SEND':
                        send_rows.append((i+1, row))
                
                logger.info(f"📊 Found {len(send_rows)} rows with Status = 'Send'")
                
                if not send_rows:
                    logger.error("❌ NO ROWS WITH STATUS = 'SEND'!")
                    logger.info("🔧 This is why triggers aren't working!")
                    logger.info("🔧 Change some rows from 'SENT' to 'Send'")
                    
                    # Show current Status values
                    status_values = {}
                    for row in data:
                        status = str(row.get('Status', '')).strip().upper()
                        status_values[status] = status_values.get(status, 0) + 1
                    
                    logger.info(f"📊 Current Status values: {status_values}")
                    
                    return False
                else:
                    logger.info("✅ Found rows with Status = 'Send'")
                    for row_num, row in send_rows[:3]:
                        logger.info(f"   Row {row_num}: {row}")
                
                # 4. Test trigger processing
                logger.info("\n4️⃣ TESTING TRIGGER PROCESSING")
                
                active_triggers = db.query(GoogleSheetTrigger).filter(
                    GoogleSheetTrigger.is_enabled == True
                ).all()
                
                logger.info(f"📊 Found {len(active_triggers)} active triggers")
                
                if active_triggers and send_rows:
                    trigger = active_triggers[0]
                    test_row_num, test_row = send_rows[0]
                    
                    logger.info(f"🧪 Testing with trigger: {trigger.trigger_id}")
                    logger.info(f"🧪 Testing with row {test_row_num}: {test_row}")
                    
                    # Check if trigger matches
                    row_value = str(test_row.get(trigger.status_column, '')).strip().upper()
                    trigger_value = str(trigger.trigger_value).strip().upper()
                    
                    logger.info(f"🧪 Trigger status_column: {trigger.status_column}")
                    logger.info(f"🧪 Trigger trigger_value: {trigger_value}")
                    logger.info(f"🧪 Row '{trigger.status_column}' value: '{row_value}'")
                    
                    if row_value == trigger_value:
                        logger.info("✅ ROW MATCHES TRIGGER!")
                        
                        # Process the row
                        row_info = {
                            'data': test_row,
                            'row_number': test_row_num
                        }
                        
                        logger.info("🧪 Processing row...")
                        result = asyncio.run(automation_service.process_row_for_trigger(sheet, trigger, row_info))
                        logger.info(f"🧪 Processing result: {result}")
                        
                    else:
                        logger.error("❌ ROW DOES NOT MATCH TRIGGER!")
                        logger.info(f"🔧 Expected: '{trigger_value}'")
                        logger.info(f"🔧 Found: '{row_value}'")
                
            except Exception as e:
                logger.error(f"❌ Error checking sheet: {e}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Check error: {e}")
        return False
    finally:
        db.close()

def show_execution_analysis():
    """Show execution analysis"""
    logger.info("\n📋 EXECUTION ANALYSIS")
    logger.info("=" * 50)
    
    logger.info("""
🔍 WHY TRIGGERS NOT EXECUTING:

1️⃣ BACKGROUND TASK NOT RUNNING:
   - No "Processing all active triggers..." logs
   - Server shows "Google Sheets automation disabled"
   - SOLUTION: Enable background task

2️⃣ NO ROWS WITH STATUS = "Send":
   - All rows have Status = "SENT"
   - Triggers look for Status = "Send"
   - SOLUTION: Change some rows to "Send"

3️⃣ TRIGGER CONFIGURATION ISSUES:
   - Triggers configured correctly now
   - Dynamic configuration applied
   - Should work if rows match

🔧 IMMEDIATE SOLUTIONS:

1️⃣ ENABLE BACKGROUND TASK:
   - Check main.py for background task
   - Ensure Google Sheets automation is enabled
   - Restart server

2️⃣ ADD STATUS = "Send" ROWS:
   - Open Google Sheet
   - Change some rows from "SENT" to "Send"
   - This gives triggers work to do

3️⃣ VERIFY DEVICE CONNECTION:
   - Device is receiving WhatsApp messages (webhook shows this)
   - But may not be connected to Engine
   - Check device connection in frontend

📱 EXPECTED AFTER FIXES:
✅ Background task runs every 30 seconds
✅ Finds Status = "Send" rows
✅ Processes triggers
✅ Sends messages
✅ Updates status to "SENT"

🔍 STEP-BY-STEP FIX:

STEP 1: ADD STATUS = "Send" ROWS
- Open Google Sheet
- Change 2-3 rows from "SENT" to "Send"
- Save changes

STEP 2: ENABLE BACKGROUND TASK
- Check main.py
- Look for background task configuration
- Restart server if needed

STEP 3: MONITOR EXECUTION
- Look for "Processing all active triggers..."
- Check for success messages
- Verify WhatsApp messages

🎉 SUCCESS INDICATORS:
✅ Background task running
✅ Status = "Send" rows found
✅ Triggers executing
✅ Messages sent
✅ WhatsApp messages received

🚀 FINAL STATUS:
The main issue is likely:
1. Background task not running
2. No Status = "Send" rows

Fix these and triggers will work!
    """)

if __name__ == "__main__":
    success = check_trigger_execution()
    show_execution_analysis()
    
    if success:
        logger.info("\n🎉 EXECUTION CHECK COMPLETE!")
        logger.info("🔧 Follow the solution steps above")
    else:
        logger.info("\n❌ EXECUTION CHECK FAILED")
        logger.info("🔧 Check the errors above")
