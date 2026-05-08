#!/usr/bin/env python3
"""
Complete diagnostic: Why messages not sent using triggers
"""

import logging
import asyncio
from datetime import datetime
from db.session import SessionLocal
from models.google_sheet import GoogleSheet, GoogleSheetTrigger
from services.google_sheets_automation import GoogleSheetsAutomationService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def complete_diagnostic():
    """Complete diagnostic of trigger message sending"""
    logger.info("🔍 COMPLETE DIAGNOSTIC: WHY MESSAGES NOT SENT")
    logger.info("=" * 70)
    
    db = SessionLocal()
    try:
        # 1. Check background task status
        logger.info("1️⃣ CHECKING BACKGROUND TASK STATUS")
        logger.info("🔄 Background task should run every 30 seconds")
        logger.info("📊 Check if process_all_active_triggers is being called")
        
        # 2. Check all active triggers
        logger.info("\n2️⃣ CHECKING ALL ACTIVE TRIGGERS")
        
        all_triggers = db.query(GoogleSheetTrigger).filter(
            GoogleSheetTrigger.is_enabled == True
        ).all()
        
        logger.info(f"📊 Found {len(all_triggers)} active triggers")
        
        for i, trigger in enumerate(all_triggers[:5]):  # Show first 5
            logger.info(f"⚡ Trigger {i+1}: {trigger.trigger_id}")
            logger.info(f"   Type: {trigger.trigger_type}")
            logger.info(f"   Device: {trigger.device_id}")
            logger.info(f"   Status column: {trigger.status_column}")
            logger.info(f"   Trigger value: {trigger.trigger_value}")
            logger.info(f"   Message: {trigger.message_template}")
            logger.info(f"   Last triggered: {trigger.last_triggered_at}")
        
        # 3. Check Google Sheet real data
        logger.info("\n3️⃣ CHECKING GOOGLE SHEET REAL DATA")
        
        if all_triggers:
            sheet = db.query(GoogleSheet).filter(
                GoogleSheet.id == all_triggers[0].sheet_id
            ).first()
            
            if sheet:
                logger.info(f"📊 Sheet: {sheet.sheet_name}")
                logger.info(f"   ID: {sheet.spreadsheet_id}")
                
                automation_service = GoogleSheetsAutomationService(db)
                
                try:
                    data, headers = automation_service.sheets_service.get_sheet_data_with_headers(
                        sheet.spreadsheet_id, "Sheet1"
                    )
                    logger.info(f"📊 Found {len(data)} rows with headers: {headers}")
                    
                    # Check for Status column
                    if 'Status' not in headers:
                        logger.error("❌ STATUS COLUMN MISSING!")
                        logger.info("🔧 SOLUTION: Add 'Status' column to Google Sheet")
                        return False
                    else:
                        logger.info("✅ Status column found")
                    
                    # Show actual data
                    logger.info("📊 Actual data in Google Sheet:")
                    for i, row in enumerate(data[:5]):  # Show first 5 rows
                        logger.info(f"   Row {i+1}: {row}")
                    
                    # Check for Send values
                    send_rows = []
                    for i, row in enumerate(data):
                        if 'Status' in row and str(row['Status']).strip().upper() == 'SEND':
                            send_rows.append((i+1, row))
                    
                    logger.info(f"📊 Found {len(send_rows)} rows with Status = 'Send'")
                    
                    if not send_rows:
                        logger.error("❌ NO ROWS WITH STATUS = 'SEND'!")
                        logger.info("🔧 SOLUTION: Set Status = 'Send' for some rows")
                        return False
                    else:
                        logger.info("✅ Found rows with Status = 'Send'")
                        for row_num, row in send_rows[:3]:  # Show first 3
                            logger.info(f"   Row {row_num}: {row}")
                    
                    # Test manual processing
                    logger.info("\n4️⃣ TESTING MANUAL PROCESSING")
                    
                    if send_rows:
                        test_row_num, test_row = send_rows[0]
                        trigger = all_triggers[0]  # Use first trigger
                        
                        logger.info(f"🧪 Testing with row {test_row_num}: {test_row}")
                        
                        row_info = {
                            'data': test_row,
                            'row_number': test_row_num
                        }
                        
                        logger.info("🧪 Processing row manually...")
                        asyncio.run(automation_service.process_row_for_trigger(sheet, trigger, row_info))
                        
                        return True
                        
                except Exception as e:
                    logger.error(f"❌ Error reading Google Sheet: {e}")
                    return False
        
        return False
        
    except Exception as e:
        logger.error(f"❌ Diagnostic error: {e}")
        return False
    finally:
        db.close()

def show_diagnostic_results():
    """Show diagnostic results"""
    logger.info("\n📋 DIAGNOSTIC RESULTS")
    logger.info("=" * 50)
    
    logger.info("""
🔍 POSSIBLE ISSUES IDENTIFIED:

1️⃣ STATUS COLUMN MISSING:
   - Google Sheet doesn't have "Status" column
   - SOLUTION: Add "Status" column (column E)

2️⃣ NO SEND VALUES:
   - No rows have Status = "Send"
   - SOLUTION: Set Status = "Send" for test rows

3️⃣ BACKGROUND TASK NOT RUNNING:
   - Background task not executing
   - SOLUTION: Restart server

4️⃣ TRIGGER CONFIGURATION:
   - Triggers not configured correctly
   - SOLUTION: Check trigger settings

5️⃣ DEVICE CONNECTION:
   - Device not actually connected
   - SOLUTION: Connect device in frontend

6️⃣ GOOGLE SHEET PERMISSIONS:
   - No access to Google Sheet
   - SOLUTION: Check permissions

🔧 IMMEDIATE FIXES:

1. ADD STATUS COLUMN:
   - Open Google Sheet
   - Add "Status" column (column E)
   - Set Status = "Send" for test rows

2. RESTART SERVER:
   - Stop the server
   - Start the server again
   - This restarts background task

3. CHECK TRIGGER SETTINGS:
   - Ensure triggers are enabled
   - Check device_id is correct
   - Check message template

4. TEST MANUAL EXECUTION:
   - Run manual test
   - Check logs for errors
   - Verify message sending

🎯 EXPECTED SUCCESS:

✅ Status column exists
✅ Rows with Status = "Send"
✅ Background task running
✅ Triggers configured correctly
✅ Device connected
✅ Messages sent successfully
✅ WhatsApp messages received

📱 EXPECTED LOGS:
🔄 Processing all active triggers...
🔍 Checking sheet 'Sheet1' for trigger conditions...
🎯 Row 1: MATCH! Status 'SEND' == 'SEND'
📱 Raw phone from sheet: 9145291501
📱 Formatted phone: +919145291501
📱 Using unofficial device 36711d22-ac2c-4e85-9b04-3f06a7d73158
📱 Personalized message: Hello {Name}! {Massage}
📤 Processing row 1 via unofficial device
📱 Sending message via unofficial device to +919145291501
✅ Message sent successfully via unofficial device to +919145291501

🚀 FINAL SOLUTION:
1. Add Status column to Google Sheet
2. Set Status = "Send" for test rows
3. Restart server to restart background task
4. Monitor logs for message sending
5. Check WhatsApp for received messages
    """)

if __name__ == "__main__":
    success = complete_diagnostic()
    show_diagnostic_results()
    
    if success:
        logger.info("\n🎉 DIAGNOSTIC COMPLETE!")
        logger.info("🔧 Follow the solution steps above")
    else:
        logger.info("\n❌ DIAGNOSTIC FAILED")
        logger.info("🔧 Check the errors above")
