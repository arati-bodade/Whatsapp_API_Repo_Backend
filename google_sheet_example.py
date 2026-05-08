#!/usr/bin/env python3
"""
Complete Google Sheet setup example for time-based triggers
"""

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def show_complete_example():
    """Show complete example setup for Google Sheet time triggers"""
    logger.info("📋 GOOGLE SHEET TIME-BASED TRIGGER SETUP EXAMPLE")
    logger.info("=" * 70)
    
    logger.info("""
🔍 YOUR GOOGLE SHEET STRUCTURE:

Copy this structure to your Google Sheet (Sheet1):

┌─────────────────────────────────────────────────────────────────────────────────────┐
│ Column A │ Column B │ Column C │ Column D │ Column E │ Column F │ Column G │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ Phone    │ Status   │ Message │ Name    │ Email    │ Notes    │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ +1234567890 │ Send     │ Hello!   │ John    │ john@e.com │ Test row │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ +9876543210 │ Send     │ Hi there!│ Jane    │ jane@e.com │ Test row │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ +1111111111 │          │          │          │          │          │ Time trigger │
├─────────────────────────────────────────────────────────────────────────────────────┤
│          │          │          │          │          │          │ Row 4      │
└─────────────────────────────────────────────────────────────────────────────────────┘

🔧 TRIGGER CONFIGURATIONS:

1️⃣ ROW-BASED TRIGGER (New Row):
{
  "trigger_type": "new_row",
  "is_enabled": true,
  "phone_column": "A",
  "status_column": "B", 
  "trigger_value": "Send",
  "message_template": "Hello {{Name}}! Welcome to our service."
}

2️⃣ ROW-BASED TRIGGER (Status Update):
{
  "trigger_type": "update_row", 
  "is_enabled": true,
  "phone_column": "A",
  "status_column": "B",
  "trigger_value": "Send",
  "message_template": "Hi {{Name}}! Your order is confirmed."
}

3️⃣ TIME-BASED TRIGGER (Every 30 minutes):
{
  "trigger_type": "time",
  "is_enabled": true,
  "phone_column": "A",
  "status_column": "B",
  "trigger_value": "Send", 
  "message_template": "Automated reminder: This is your scheduled message.",
  "execution_interval": 1800
}

4️⃣ TIME-BASED TRIGGER (Every hour for important updates):
{
  "trigger_type": "time",
  "is_enabled": true,
  "phone_column": "A", 
  "status_column": "B",
  "trigger_value": "Urgent",
  "message_template": "URGENT: {{Name}}! Please check your account immediately.",
  "execution_interval": 3600
}

🚀 EXPECTED BEHAVIOR:

📱 ROW-BASED TRIGGERS:
- Trigger 1️⃣: Fires when new row added with "Send" in Column B
  → Sends: "Hello {{Name}}! Welcome to our service."
- Trigger 2️⃣: Fires when Column B changes to "Send"  
  → Sends: "Hi {{Name}}! Your order is confirmed."

🕐 TIME-BASED TRIGGERS:
- Trigger 3️⃣: Fires every 30 minutes
  → Checks all rows where Column B = "Send"
  → Sends: "Automated reminder: This is your scheduled message."
- Trigger 4️⃣: Fires every hour
  → Checks all rows where Column B = "Urgent"  
  → Sends: "URGENT: {{Name}}! Please check your account immediately."

📋 HOW TO USE:

1️⃣ SET UP YOUR SHEET:
   - Copy the structure above to your Google Sheet
   - Make sure Column A has phone numbers
   - Make sure Column B has status values
   - Add test data as shown

2️⃣ CREATE TRIGGERS:
   - Use the API or frontend to create triggers
   - Use the exact JSON configurations shown above
   - Set appropriate execution intervals

3️⃣ TEST AUTOMATION:
   - Add new rows with "Send" in Column B
   - Change existing statuses from "Send" to "Urgent"
   - Wait for time-based triggers to execute
   - Check server logs for execution messages

4️⃣ MONITOR RESULTS:
   - Watch for: "🕐 Processing time-based trigger {trigger_id}"
   - Look for: "🚀 Time trigger {trigger_id} executing NOW"
   - Verify WhatsApp messages are received
   - Check trigger history in database

🎯 EXAMPLE SCENARIOS:

📱 CUSTOMER ONBOARDING:
- When new customer added → Row 1️⃣ triggers
- Sends welcome message automatically

📦 ORDER UPDATES:
- When order status changes → Row 2️⃣ triggers  
- Sends confirmation automatically

📅 APPOINTMENT REMINDERS:
- Time trigger 3️⃣ fires every hour
- Checks for "Urgent" status
- Sends automated reminders

📢 SYSTEM ALERTS:
- Time trigger 4️⃣ fires every 30 minutes
- Sends system notifications
- Handles automated monitoring

💡 TIPS FOR SUCCESS:
- Use descriptive message templates with {{Name}} placeholders
- Set appropriate intervals (30min, 1hour, etc.)
- Test with small data sets first
- Monitor logs for debugging
- Keep phone numbers in Column A formatted (+country code)
- Use different trigger values for different message types

🔧 TROUBLESHOOTING:
- If triggers don't fire → Check column names match exactly
- If no messages → Check WhatsApp API configuration
- If errors → Check server logs and trigger history
- If timing wrong → Check execution_interval settings
- If duplicates → Check for overlapping trigger conditions

This setup will give you fully functional time-based triggers!
    """)

if __name__ == "__main__":
    show_complete_example()
