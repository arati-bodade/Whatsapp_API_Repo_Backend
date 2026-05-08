#!/usr/bin/env python3
"""
Complete Trigger System Information Guide
"""

import logging
from db.session import SessionLocal
from models.google_sheet import GoogleSheet, GoogleSheetTrigger, GoogleSheetTriggerHistory
from models.device import Device

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def complete_trigger_information():
    """Provide complete trigger system information"""
    logger.info("📚 COMPLETE TRIGGER SYSTEM INFORMATION")
    logger.info("=" * 80)
    
    db = SessionLocal()
    try:
        # 1. Trigger System Overview
        logger.info("1️⃣ TRIGGER SYSTEM OVERVIEW")
        logger.info("""
🔧 WHAT IS THE TRIGGER SYSTEM:
The trigger system automates WhatsApp message sending based on Google Sheet data changes.
It monitors Google Sheets and sends messages when specific conditions are met.

🎯 KEY COMPONENTS:
1. Google Sheets - Data source with trigger conditions
2. Triggers - Rules for when to send messages
3. Devices - WhatsApp devices that send messages
4. Background Task - Processes triggers every 30 seconds
5. Trigger History - Logs all message attempts

🔄 WORKFLOW:
1. Google Sheet data changes (Status = "Send")
2. Background task detects changes
3. Trigger conditions are evaluated
4. Messages sent via WhatsApp devices
5. Status updated to "SENT"
6. History records created
        """)
        
        # 2. Trigger Types
        logger.info("\n2️⃣ TRIGGER TYPES")
        logger.info("""
📋 AVAILABLE TRIGGER TYPES:

1️⃣ NEW_ROW:
   - Fires when new rows are added to Google Sheet
   - Checks for Status = "Send" in new rows
   - Sends message for each new matching row

2️⃣ UPDATE_ROW:
   - Fires when existing rows are updated
   - Checks for Status = "Send" in updated rows
   - Sends message for each updated matching row

3️⃣ TIME:
   - Fires at specific times
   - Uses Time column for scheduling
   - Sends message at scheduled times

🔧 TRIGGER CONFIGURATION:
- status_column: Column to monitor (usually "Status")
- trigger_value: Value to match (usually "Send")
- message_template: Message format with placeholders
- device_id: WhatsApp device to send messages
        """)
        
        # 3. Google Sheet Format
        logger.info("\n3️⃣ GOOGLE SHEET FORMAT")
        logger.info("""
📊 REQUIRED GOOGLE SHEET FORMAT:

🔧 COLUMN HEADERS (EXACT SPELLING):
| Phone | Name | Time | Massage | Status |
|-------|-------|-------|---------|--------|

📝 COLUMN DESCRIPTIONS:
1. Phone: Phone number (without country code)
   - Format: 9145291501
   - System adds: +91
   - Final: +919145291501

2. Name: Recipient name (for personalization)
   - Used in message template: {Name}
   - Example: "John Doe"

3. Time: Time for scheduling (optional)
   - Format: 10.30 AM
   - Used by TIME triggers
   - 24-hour format also works

4. Massage: Message content (note: "Massage" not "Message")
   - Used in message template: {Massage}
   - Example: "Hello! How are you?"

5. Status: Trigger status (CRITICAL)
   - Values: "Send" (triggers message) or "SENT" (already sent)
   - Case-sensitive: "Send" not "send"
   - System changes "Send" → "SENT" after sending

🎯 TRIGGER WORKFLOW:
1. Add row with Status = "Send"
2. Background task detects change
3. Trigger fires and sends message
4. Status automatically changes to "SENT"
        """)
        
        # 4. Current System Status
        logger.info("\n4️⃣ CURRENT SYSTEM STATUS")
        
        # Check Google Sheets
        sheets = db.query(GoogleSheet).all()
        logger.info(f"📊 Google Sheets: {len(sheets)} configured")
        
        for sheet in sheets:
            logger.info(f"   Sheet: {sheet.sheet_name}")
            logger.info(f"   ID: {sheet.id}")
            logger.info(f"   Status: {sheet.status}")
            logger.info(f"   Triggers: {len(sheet.triggers)}")
        
        # Check Triggers
        triggers = db.query(GoogleSheetTrigger).filter(
            GoogleSheetTrigger.is_enabled == True
        ).all()
        logger.info(f"\n📊 Active Triggers: {len(triggers)}")
        
        trigger_types = {}
        device_usage = {}
        
        for trigger in triggers:
            trigger_type = trigger.trigger_type
            trigger_types[trigger_type] = trigger_types.get(trigger_type, 0) + 1
            
            device_id = str(trigger.device_id) if trigger.device_id else "None"
            device_usage[device_id] = device_usage.get(device_id, 0) + 1
        
        logger.info(f"   Trigger Types: {trigger_types}")
        logger.info(f"   Device Usage: {device_usage}")
        
        # Check Devices
        devices = db.query(Device).all()
        logger.info(f"\n📊 Available Devices: {len(devices)}")
        
        for device in devices:
            logger.info(f"   Device: {device.device_name}")
            logger.info(f"   ID: {device.device_id}")
            logger.info(f"   Status: {device.session_status}")
            logger.info(f"   Type: {device.device_type}")
            logger.info(f"   Active: {device.is_active}")
        
        # Check Recent History
        recent_history = db.query(GoogleSheetTriggerHistory).order_by(
            GoogleSheetTriggerHistory.triggered_at.desc()
        ).limit(10).all()
        
        logger.info(f"\n📊 Recent Trigger History: {len(recent_history)} records")
        
        if recent_history:
            status_counts = {}
            for record in recent_history:
                status = str(record.status).upper()
                status_counts[status] = status_counts.get(status, 0) + 1
            
            logger.info(f"   Recent Status: {status_counts}")
        else:
            logger.info("   No recent history records")
        
        # 5. Message Templates
        logger.info("\n5️⃣ MESSAGE TEMPLATES")
        logger.info("""
📝 MESSAGE TEMPLATE SYSTEM:

🔧 PLACEHOLDERS:
{Phone} - Recipient phone number
{Name} - Recipient name
{Time} - Time value
{Massage} - Message content

🔧 EXAMPLE TEMPLATES:
1. Simple: "Hello {Name}! {Massage}"
2. Personal: "Hi {Name}, your message '{Massage}' was sent at {Time}"
3. Dynamic: "Dear {Name}, regarding your phone {Phone}: {Massage}"

🔧 TEMPLATE PROCESSING:
1. Trigger reads template from trigger.message_template
2. Replaces placeholders with row data
3. Sends personalized message
4. Logs final message in history

🔧 DYNAMIC CONFIGURATION:
- template_name: Unique identifier for each trigger
- language_code: Auto-detected from content
- header_param_columns: ['Name', 'Phone', 'Time']
- body_param_columns: ['Massage', 'Status']
        """)
        
        # 6. Background Task
        logger.info("\n6️⃣ BACKGROUND TASK")
        logger.info("""
🔄 BACKGROUND TASK SYSTEM:

⏰ EXECUTION SCHEDULE:
- Runs every 30 seconds
- Processes all active triggers
- Monitors Google Sheet changes
- Sends messages automatically

🔄 TASK PROCESSING:
1. process_all_active_triggers() called
2. Each trigger checks its conditions
3. Matching rows are processed
4. Messages sent via devices
5. Status updated in Google Sheet
6. History records created

🔄 LOGGING:
- "Processing all active triggers..."
- "Row X: MATCH! Status 'SEND' == 'SEND'"
- "Message sent successfully"
- "Updated row X status to 'SENT'"

🔄 ERROR HANDLING:
- Device connection errors logged
- Failed messages marked as FAILED
- Retry mechanisms in place
- Graceful error handling
        """)
        
        # 7. Troubleshooting
        logger.info("\n7️⃣ TROUBLESHOOTING GUIDE")
        logger.info("""
🔧 COMMON ISSUES AND SOLUTIONS:

❌ MESSAGES NOT SENDING:
1. Check Status column values (must be "Send")
2. Verify device connection to WhatsApp Engine
3. Check trigger configurations
4. Review background task logs

❌ DEVICE NOT FOUND:
1. Verify device_id format (UUID)
2. Check device exists in database
3. Ensure device is connected
4. Update triggers with correct device_id

❌ TRIGGER HISTORY EMPTY:
1. Check if triggers are enabled
2. Verify Status = "Send" rows exist
3. Check background task is running
4. Review error logs

❌ GOOGLE SHEET ISSUES:
1. Verify column headers (exact spelling)
2. Check sheet permissions
3. Ensure Status column exists
4. Validate data formats

🔧 DEBUGGING STEPS:
1. Check server logs for errors
2. Verify trigger configurations
3. Test device connections
4. Validate Google Sheet data
5. Run manual trigger tests
        """)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Information error: {e}")
        return False
    finally:
        db.close()

def show_quick_reference():
    """Show quick reference guide"""
    logger.info("\n📋 QUICK REFERENCE GUIDE")
    logger.info("=" * 50)
    
    logger.info("""
🚀 QUICK START:

1️⃣ SETUP GOOGLE SHEET:
   Headers: Phone | Name | Time | Massage | Status
   Add rows with Status = "Send"

2️⃣ CONFIGURE TRIGGERS:
   status_column: "Status"
   trigger_value: "Send"
   device_id: Your WhatsApp device ID

3️⃣ START SYSTEM:
   Background task runs every 30 seconds
   Monitors Google Sheet changes
   Sends messages automatically

🎯 SUCCESS INDICATORS:
✅ "Processing all active triggers..." logs
✅ "Row X: MATCH!" logs
✅ "Message sent successfully" logs
✅ WhatsApp messages received
✅ Status changes to "SENT"

📱 EXPECTED BEHAVIOR:
1. Add Status = "Send" to Google Sheet
2. Wait 30 seconds
3. Receive WhatsApp message
4. Status changes to "SENT"
5. History record created

🔧 MAINTENANCE:
- Monitor trigger history
- Check device connections
- Verify Google Sheet data
- Review error logs
    """)

if __name__ == "__main__":
    complete_trigger_information()
    show_quick_reference()
    
    logger.info("\n🎉 TRIGGER SYSTEM INFORMATION COMPLETE!")
    logger.info("📚 Refer to this guide for all trigger system operations")
