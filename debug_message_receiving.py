#!/usr/bin/env python3
"""
Debug why messages aren't being received on your device
"""

import logging
import asyncio
from datetime import datetime
from db.session import SessionLocal
from models.google_sheet import GoogleSheet, GoogleSheetTrigger
from services.google_sheets_automation import GoogleSheetsAutomationService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_message_receiving():
    """Debug why messages aren't being received"""
    logger.info("🔍 DEBUGGING: WHY MESSAGES NOT RECEIVED")
    logger.info("=" * 70)
    
    db = SessionLocal()
    try:
        # Your device ID
        your_device_id = "36711d22-ac2c-4e85-9b04-3f06a7d73158"
        
        logger.info(f"📱 Your Device ID: {your_device_id}")
        
        # 1. Check if your device exists in database
        logger.info("\n1️⃣ CHECKING DEVICE IN DATABASE")
        
        from models.device import Device
        device = db.query(Device).filter(
            Device.device_id == your_device_id
        ).first()
        
        if not device:
            logger.error("❌ Device not found in database!")
            logger.info("🔧 SOLUTION: Create device record first")
            return False
        
        logger.info(f"✅ Device found: {device.device_name}")
        logger.info(f"   Status: {device.session_status}")
        logger.info(f"   Type: {device.device_type}")
        logger.info(f"   Created: {device.created_at}")
        logger.info(f"   Updated: {device.updated_at}")
        
        # 2. Check triggers using your device
        logger.info("\n2️⃣ CHECKING TRIGGERS USING YOUR DEVICE")
        
        triggers = db.query(GoogleSheetTrigger).filter(
            GoogleSheetTrigger.device_id == your_device_id,
            GoogleSheetTrigger.is_enabled == True
        ).all()
        
        logger.info(f"📊 Found {len(triggers)} triggers using your device")
        
        for trigger in triggers:
            logger.info(f"⚡ Trigger: {trigger.trigger_id}")
            logger.info(f"   Type: {trigger.trigger_type}")
            logger.info(f"   Status column: {trigger.status_column}")
            logger.info(f"   Trigger value: {trigger.trigger_value}")
            logger.info(f"   Message: {trigger.message_template}")
        
        if not triggers:
            logger.error("❌ No triggers using your device!")
            logger.info("🔧 SOLUTION: Update triggers to use your device ID")
            return False
        
        # 3. Test Google Sheet structure
        logger.info("\n3️⃣ CHECKING GOOGLE SHEET STRUCTURE")
        
        if triggers:
            sheet = db.query(GoogleSheet).filter(
                GoogleSheet.id == triggers[0].sheet_id
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
                        logger.error("❌ Status column not found in Google Sheet!")
                        logger.info("🔧 SOLUTION: Add 'Status' column to Google Sheet")
                        logger.info("   - Open your Google Sheet")
                        logger.info("   - Add 'Status' column (column E)")
                        logger.info("   - Set Status = 'Send' for rows to trigger")
                        return False
                    else:
                        logger.info("✅ Status column found in Google Sheet")
                    
                    # Check for matching Status values
                    status_values = []
                    for row in data:
                        if 'Status' in row and row['Status']:
                            status_values.append(str(row['Status']).strip().upper())
                    
                    logger.info(f"📊 Status values found: {list(set(status_values))}")
                    
                    if 'SEND' not in status_values:
                        logger.error("❌ No rows with Status = 'Send' found!")
                        logger.info("🔧 SOLUTION: Set Status = 'Send' for test rows")
                        logger.info("   - Add test rows to Google Sheet")
                        logger.info("   - Set Status column to 'Send'")
                        logger.info("   - Include Phone, Name, Message columns")
                        return False
                    else:
                        logger.info("✅ Found rows with Status = 'Send'")
                    
                    # Show first few rows
                    logger.info("📊 First 3 rows:")
                    for i, row in enumerate(data[:3]):
                        logger.info(f"   Row {i+1}: {row}")
                        
                except Exception as e:
                    logger.error(f"❌ Error reading Google Sheet: {e}")
                    return False
        
        # 4. Test manual trigger execution
        logger.info("\n4️⃣ TESTING MANUAL TRIGGER EXECUTION")
        
        if triggers and sheet:
            trigger = triggers[0]
            
            # Create test row data
            test_row_data = {
                'Phone': '9145291501',  # Your test number
                'Name': 'Test User',
                'Time': '5.30 PM',
                'Massage': 'Test message - FINAL DEBUG TEST',
                'Status': 'Send'
            }
            
            row_info = {
                'data': test_row_data,
                'row_number': 1
            }
            
            logger.info(f"🧪 Test row data: {test_row_data}")
            
            # Process the row
            automation_service = GoogleSheetsAutomationService(db)
            
            logger.info("🧪 Processing test row...")
            result = asyncio.run(automation_service.process_row_for_trigger(sheet, trigger, row_info))
            
            logger.info(f"🧪 Processing result: {result}")
        
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
🔍 POSSIBLE REASIES FOR NOT RECEIVING MESSAGES:

1️⃣ STATUS COLUMN MISSING:
   - Google Sheet doesn't have "Status" column
   - SOLUTION: Add "Status" column (column E)

2️⃣ NO SEND VALUES:
   - No rows have Status = "Send"
   - SOLUTION: Set Status = "Send" for test rows

3️⃣ WRONG PHONE NUMBERS:
   - Phone numbers not in correct format
   - SOLUTION: Use format like 9145291501 (auto-formatted to +919145291501)

4️⃣ DEVICE NOT CONNECTED:
   - Device not actually connected to WhatsApp
   - SOLUTION: Connect device in frontend

5️⃣ TRIGGER CONFIGURATION:
   - Triggers not configured correctly
   - SOLUTION: Check trigger settings

🔧 IMMEDIATE FIXES:

1. ADD STATUS COLUMN:
   - Open Google Sheet: 1eF28T3dsJ78IaDSVQI0T3wvCD9lQBkqHhzjgYE1mEjw
   - Add "Status" column (column E)
   - Set Status = "Send" for test rows

2. VERIFY PHONE NUMBERS:
   - Use format: 9145291501
   - System adds +91 automatically
   - Final format: +919145291501

3. CHECK DEVICE CONNECTION:
   - Go to WhatsApp device management
   - Ensure your device is connected
   - Reconnect if needed

4. TEST WITH SPECIFIC NUMBER:
   - Add row with your phone number
   - Set Status = "Send"
   - Monitor for message

📱 EXPECTED RESULT:
- Background task finds Status = "Send" rows
- Phone formatted: 9145291501 → +919145291501
- Message personalized and sent
- You receive WhatsApp message

🎯 SUCCESS INDICATORS:
✅ Status column exists
✅ Rows with Status = "Send"
✅ Phone numbers formatted correctly
✅ Device connected
✅ Messages sent successfully
✅ WhatsApp messages received

🚀 TEST STEPS:
1. Add Status column to Google Sheet
2. Add test row with your phone number
3. Set Status = "Send"
4. Wait 30 seconds
5. Check WhatsApp for message
    """)

if __name__ == "__main__":
    success = debug_message_receiving()
    show_debug_solution()
    
    if success:
        logger.info("\n🎉 DEBUG COMPLETE!")
        logger.info("🔧 Follow the solution steps above")
    else:
        logger.info("\n❌ DEBUG FAILED")
        logger.info("🔧 Check the errors above")
