#!/usr/bin/env python3
"""
Time-based trigger setup for specific times
"""

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def show_scheduled_time_triggers():
    """Show how to set up time-based triggers for specific times"""
    logger.info("⏰ SCHEDULED TIME-BASED TRIGGERS")
    logger.info("=" * 70)
    
    logger.info("""
🔍 SETUP SPECIFIC TIMES INSTEAD OF INTERVALS:

Instead of using execution_interval (repeats every X minutes), 
you can use a time column to specify exact times.

📋 GOOGLE SHEET STRUCTURE:

┌─────────────────────────────────────────────────────────────┐
│ Column A │ Column B │ Column C │ Column D │ Column E │
├─────────────────────────────────────────────────────────────┤
│ Time     │ Status   │ Message │ Name    │ Email    │ Notes   │
├─────────────────────────────────────────────────────────────┤
│ 09:00    │ Send     │ Hi!     │ John    │ john@e.com │ Morning  │
│ 12:00    │ Send     │ Lunch    │ Jane    │ jane@e.com │ Noon    │
│ 15:00    │ Send     │ Break    │ Mike    │ mike@e.com │ Afternoon│
│ 18:00    │ Send     │ Dinner   │ Sarah   │ sarah@e.com │ Evening  │
└─────────────────────────────────────────────────────────────┘

🔧 TRIGGER CONFIGURATION:

1️⃣ TIME-BASED TRIGGER (Specific Times):
{
  "trigger_type": "time",
  "is_enabled": true,
  "phone_column": "A",
  "status_column": "B",
  "message_template": "Good {{Name}}! It's {{Time}}.",
  "trigger_config": {
    "schedule_column": "Time",  // Use this column for specific times
    "specific_times": ["09:00", "12:00", "15:00", "18:00"]  // Optional: specific times
  }
}

2️⃣ TIME-BASED TRIGGER (Every 30 minutes):
{
  "trigger_type": "time", 
  "is_enabled": true,
  "phone_column": "A",
  "status_column": "B",
  "message_template": "Automated reminder: {{Time}}",
  "execution_interval": 1800  // Every 30 minutes
}

3️⃣ TIME-BASED TRIGGER (Every hour):
{
  "trigger_type": "time",
  "is_enabled": true,
  "phone_column": "A", 
  "status_column": "B",
  "message_template": "Hourly update: {{Time}}",
  "execution_interval": 3600  // Every hour
}

📋 HOW TO SET UP SPECIFIC TIMES:

1️⃣ ADD TIME COLUMN (Column C):
   - Add a "Time" column to your Google Sheet
   - Format times as HH:MM (24-hour format)
   - Example: "09:00", "12:30", "15:45"

2️⃣ ADD STATUS COLUMN (Column B):
   - Add a "Status" column to your Google Sheet
   - Use values: "Send", "Processed", "Scheduled"

3️⃣ CONFIGURE TRIGGER:
   Use the "specific_times" configuration in trigger_config
   - The system will check the Time column at each run
   - When current time matches a specific time → trigger executes

📋 EXAMPLE SHEET SETUP:

Copy this to your Google Sheet:

┌─────────────────────────────────────────────────────────────┐
│ Column A │ Column B │ Column C │ Column D │ Column E │
├─────────────────────────────────────────────────────────────┤
│ Name     │ Time     │ Status   │ Message                    │ Notes   │
├─────────────────────────────────────────────────────────────┤
│ John     │ 09:00   │ Send     │ Good John! It's 09:00. │         │
│ Jane     │ 12:00   │ Send     │ Good Jane! It's 12:00. │         │
│ Mike     │ 15:00   │ Send     │ Good Mike! It's 15:00. │         │
│ Sarah    │ 18:00   │ Send     │ Good Sarah! It's 18:00. │         │
└─────────────────────────────────────────────────────────────┘

🔧 TRIGGER CREATION:

Use this JSON to create a time-based trigger with specific times:

POST /api/google-sheets/{sheet_id}/triggers
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json

{
  "trigger_type": "time",
  "is_enabled": true,
  "phone_column": "A",
  "status_column": "B", 
  "trigger_value": "Send",
  "message_template": "Good {{Name}}! It's {{Time}}.",
  "trigger_config": {
    "schedule_column": "Time",
    "specific_times": ["09:00", "12:00", "15:00", "18:00"]
  }
}

🚀 EXPECTED BEHAVIOR:

- At 09:00 → Sends "Good John! It's 09:00" to +1234567890
- At 12:00 → Sends "Good Jane! It's 12:00" to +9876543210
- At 15:00 → Sends "Good Mike! It's 15:00" to +1111111111
- At 18:00 → Sends "Good Sarah! It's 18:00" to +2222222222

📋 MONITORING:

Watch server logs for:
"🕐 Processing time-based trigger {trigger_id}"
"🚀 Time trigger {trigger_id} executing NOW"
"✅ Time trigger {trigger_id} executed successfully"
"📱 Sending messages via Official WhatsApp API"

🎯 BENEFITS:
✅ Send messages at exact times you want
✅ Different messages for different times of day
✅ More control over message timing
✅ Better customer experience with scheduled communications

🔧 IMPLEMENTATION NOTE:
The specific_times feature is already implemented in the time trigger logic.
When the system finds a "specific_times" array in trigger_config,
it will check those exact times instead of using intervals.
    """)

if __name__ == "__main__":
    show_scheduled_time_triggers()
