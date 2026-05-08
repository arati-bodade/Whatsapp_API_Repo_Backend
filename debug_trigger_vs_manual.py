#!/usr/bin/env python3
"""
Debug why triggers aren't working but single messages work
"""

import logging
import asyncio
from datetime import datetime
from db.session import SessionLocal
from models.google_sheet import GoogleSheet, GoogleSheetTrigger
from services.google_sheets_automation import GoogleSheetsAutomationService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_trigger_vs_manual():
    """Debug why triggers not working but manual messages work"""
    logger.info("🔍 DEBUG: TRIGGERS VS MANUAL MESSAGES")
    logger.info("=" * 70)
    
    db = SessionLocal()
    try:
        # 1. Check if background task is actually running
        logger.info("1️⃣ CHECKING BACKGROUND TASK")
        logger.info("🔄 Background task should call process_all_active_triggers() every 30 seconds")
        logger.info("🔍 Let's test this manually...")
        
        # 2. Run background task manually
        logger.info("\n2️⃣ RUNNING BACKGROUND TASK MANUALLY")
        
        automation_service = GoogleSheetsAutomationService(db)
        
        logger.info("🔄 Calling process_all_active_triggers()...")
        result = asyncio.run(automation_service.process_all_active_triggers())
        
        logger.info(f"🔄 Background task result: {result}")
        
        # 3. Check what triggers are actually being processed
        logger.info("\n3️⃣ CHECKING TRIGGER PROCESSING")
        
        active_triggers = db.query(GoogleSheetTrigger).filter(
            GoogleSheetTrigger.is_enabled == True
        ).all()
        
        logger.info(f"📊 Found {len(active_triggers)} active triggers")
        
        for i, trigger in enumerate(active_triggers[:3]):  # Show first 3
            logger.info(f"⚡ Trigger {i+1}: {trigger.trigger_id}")
            logger.info(f"   Type: {trigger.trigger_type}")
            logger.info(f"   Device: {trigger.device_id}")
            logger.info(f"   Status column: {trigger.status_column}")
            logger.info(f"   Trigger value: {trigger.trigger_value}")
            logger.info(f"   Message: {trigger.message_template}")
            logger.info(f"   Last triggered: {trigger.last_triggered_at}")
        
        # 4. Check Google Sheet data
        logger.info("\n4️⃣ CHECKING GOOGLE SHEET DATA")
        
        if active_triggers:
            sheet = db.query(GoogleSheet).filter(
                GoogleSheet.id == active_triggers[0].sheet_id
            ).first()
            
            if sheet:
                logger.info(f"📊 Sheet: {sheet.sheet_name}")
                
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
                        logger.info("🔧 Add Status = 'Send' to some rows")
                        return False
                    else:
                        logger.info("✅ Found rows with Status = 'Send'")
                        for row_num, row in send_rows[:3]:
                            logger.info(f"   Row {row_num}: {row}")
                    
                    # Check trigger configurations
                    logger.info("\n5️⃣ CHECKING TRIGGER CONFIGURATIONS")
                    
                    for trigger in active_triggers[:3]:
                        logger.info(f"⚡ Trigger: {trigger.trigger_id}")
                        logger.info(f"   Status column: {trigger.status_column}")
                        logger.info(f"   Trigger value: {trigger.trigger_value}")
                        
                        # Check if trigger configuration matches sheet
                        if trigger.status_column not in headers:
                            logger.error(f"❌ Status column '{trigger.status_column}' not in sheet!")
                            continue
                        
                        # Check if trigger value exists in sheet
                        trigger_values = set()
                        for row in data:
                            if trigger.status_column in row and row[trigger.status_column]:
                                trigger_values.add(str(row[trigger.status_column]).strip().upper())
                        
                        logger.info(f"   Available values in column '{trigger.status_column}': {list(trigger_values)}")
                        
                        if trigger.trigger_value not in trigger_values:
                            logger.error(f"❌ Trigger value '{trigger.trigger_value}' not found in sheet!")
                            logger.info(f"   Available: {list(trigger_values)}")
                        else:
                            logger.info(f"✅ Trigger value '{trigger.trigger_value}' exists in sheet")
                        
                        logger.info("")
                        
                except Exception as e:
                    logger.error(f"❌ Error checking sheet: {e}")
                    return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Debug error: {e}")
        return False
    finally:
        db.close()

def show_debug_solution():
    """Show debug solution"""
    logger.info("\n🔧 DEBUG SOLUTION")
    logger.info("=" * 50)
    
    logger.info("""
🔍 WHY TRIGGERS NOT WORKING:

1️⃣ BACKGROUND TASK NOT RUNNING:
   - Background task not calling process_all_active_triggers()
   - SOLUTION: Restart server to restart background task

2️⃣ NO ROWS WITH STATUS = "Send":
   - All rows have Status = "SENT" or other values
   - SOLUTION: Set Status = "Send" for test rows

3️⃣ TRIGGER CONFIGURATION MISMATCH:
   - Trigger status_column doesn't match sheet columns
   - Trigger trigger_value doesn't exist in sheet
   - SOLUTION: Update trigger configuration

4️⃣ TRIGGER TYPE ISSUES:
   - Time triggers not configured properly
   - Row triggers not finding matching rows
   - SOLUTION: Check trigger configuration

🔧 IMMEDIATE FIXES:

1️⃣ CHECK BACKGROUND TASK:
   - Look for "Processing all active triggers..." in logs
   - If not seen, restart server

2️⃣ ADD STATUS = "Send" ROWS:
   - Add new rows with Status = "Send"
   - Or change existing rows to "Send"

3️⃣ VERIFY TRIGGER CONFIG:
   - Status column should be "Status"
   - Trigger value should be "Send"
   - Message template should have content

4️⃣ TEST MANUAL BACKGROUND TASK:
   - Run process_all_active_triggers() manually
   - Check if it processes rows

📱 EXPECTED SUCCESS LOGS:
🔄 Processing all active triggers...
🔍 Checking sheet 'Sheet1' for trigger conditions...
🎯 Row 1: MATCH! Status 'SEND' == 'SEND'
📱 Raw phone from sheet: 9145291501
📱 Formatted phone: +919145291501
📱 Using unofficial device 36711d22-ac2c-4e85-9b04-3f06a7d73158
📱 Personalized message: Hello {Name}! {Message}
📤 Processing row 1 via unofficial device
📱 Sending message via unofficial device to +919145291501
✅ Message sent successfully via unofficial device to +919145291501

🎯 SOLUTION:
1. Run this debug script
2. Check if background task runs
3. Add Status = "Send" rows if needed
4. Verify trigger configuration
5. Test manual background task execution

🚀 EXPECTED RESULT:
- Background task processes triggers
- Finds rows with Status = "Send"
- Sends messages successfully
- You receive WhatsApp messages
    """)

if __name__ == "__main__":
    success = debug_trigger_vs_manual()
    show_debug_solution()
    
    if success:
        logger.info("\n🎉 DEBUG COMPLETE!")
        logger.info("🔧 Follow the solution steps above")
    else:
        logger.info("\n❌ DEBUG FAILED")
        logger.info("🔧 Check the errors above")
