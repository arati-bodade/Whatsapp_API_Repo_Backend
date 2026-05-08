#!/usr/bin/env python3
"""
Complete detailed explanation of how time-based triggers work
"""

import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def explain_trigger_system():
    """Complete explanation of the trigger system"""
    logger.info("🔍 COMPLETE TIME-BASED TRIGGER SYSTEM EXPLANATION")
    logger.info("=" * 80)
    
    logger.info("""
🎯 OVERVIEW:
The time-based trigger system automatically sends WhatsApp messages at specified times
by checking your Google Sheet data and executing triggers when conditions are met.

📋 SYSTEM ARCHITECTURE:

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                    TIME-BASED TRIGGER SYSTEM ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  1. BACKGROUND TASK (Every 30 seconds)                                             │
│     ↓                                                                              │
│  2. process_all_active_triggers()                                                   │
│     ↓                                                                              │
│  3. process_sheet_triggers() for each active sheet                                 │
│     ↓                                                                              │
│  4. Check trigger type:                                                           │
│     ├─ TIME triggers → should_run_time_trigger()                                   │
│     └─ ROW triggers → row condition checking                                        │
│     ↓                                                                              │
│  5. If condition met → process_single_trigger()                                    │
│     ↓                                                                              │
│  6. Send message via Official WhatsApp API                                          │
│     ↓                                                                              │
│  7. Update trigger history and timestamps                                         │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘

🔧 DETAILED WORKFLOW:

1️⃣ BACKGROUND TASK EXECUTION:
   - Runs every 30 seconds (configurable)
   - Located in: services/background_task_manager.py
   - Calls: process_all_active_triggers()
   - Creates fresh database session for each cycle

2️⃣ TRIGGER DISCOVERY:
   - Finds all active sheets (status = 'ACTIVE')
   - Gets all enabled triggers for each sheet
   - Separates time-based from row-based triggers

3️⃣ TIME TRIGGER LOGIC (should_run_time_trigger):
   - Reads trigger_config for timing information
   - Two modes: INTERVAL vs SPECIFIC_TIMES
   - INTERVAL: last_triggered_at + interval_seconds
   - SPECIFIC_TIMES: checks if current_time matches any specific time

4️⃣ MESSAGE EXECUTION (process_single_trigger):
   - Fetches Google Sheet data
   - Filters rows based on trigger conditions
   - Builds personalized messages with templates
   - Sends via Official WhatsApp API
   - Updates trigger history

📋 TRIGGER CONFIGURATION OPTIONS:

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           TRIGGER CONFIGURATION OPTIONS                            │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  BASIC SETTINGS:                                                                   │
│  ├─ trigger_type: "time"                                                           │
│  ├─ is_enabled: true/false                                                         │
│  ├─ phone_column: "Phone" (column name)                                            │
│  ├─ status_column: "Status" (column name)                                          │
│  ├─ trigger_value: "Send" (value to match)                                         │
│  ├─ message_template: "Hello {{Name}}!"                                            │
│                                                                                     │
│  TIMING OPTIONS:                                                                   │
│  ├─ execution_interval: 3600 (seconds)                                             │
│  │   └─ Repeats every X seconds                                                    │
│  ├─ trigger_config:                                                                │
│  │   ├─ schedule_column: "Time"                                                    │
│  │   ├─ specific_times: ["09:00", "12:00", "15:00"]                               │
│  │   └─ interval: 1800 (alternative to execution_interval)                        │
│                                                                                     │
│  ADVANCED OPTIONS:                                                                 │
│  ├─ webhook_url: "https://example.com/webhook"                                    │
│  ├─ trigger_column: "CustomColumn"                                                │
│  └─ device_id: null (Official API only)                                           │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘

🕐 TIMING MODES EXPLAINED:

1️⃣ INTERVAL MODE (Regular Repeating):
   {
     "trigger_type": "time",
     "execution_interval": 3600,  // Every hour
     "message_template": "Hourly reminder!"
   }
   → Fires every hour, repeats continuously

2️⃣ SPECIFIC TIMES MODE (Exact Times):
   {
     "trigger_type": "time",
     "trigger_config": {
       "specific_times": ["09:00", "12:00", "15:00", "18:00"]
     }
   }
   → Fires only at those exact times daily

3️⃣ SCHEDULE COLUMN MODE (Time Column in Sheet):
   {
     "trigger_type": "time",
     "trigger_config": {
       "schedule_column": "Time"
     }
   }
   → Checks Time column in each row for matching times

📊 GOOGLE SHEET INTEGRATION:

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           GOOGLE SHEET DATA STRUCTURE                              │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  REQUIRED COLUMNS:                                                                 │
│  ├─ Phone: +1234567890 (with country code)                                         │
│  ├─ Status: "Send" (trigger condition)                                             │
│  ├─ Time: "09:00" (optional, for time column mode)                                 │
│  ├─ Name: "John" (optional, for personalization)                                 │
│  └─ Message: "Custom message" (optional)                                          │
│                                                                                     │
│  EXAMPLE ROWS:                                                                     │
│  │ Phone      │ Status │ Time  │ Name  │ Message                    │ Notes       │
│  │------------│--------│-------│-------│----------------------------│-------------│
│  │ +1234567890│ Send   │ 09:00 │ John  │ Good morning!             │ Morning msg │
│  │ +9876543210│ Send   │ 12:00 │ Jane  │ Lunch time!               │ Lunch msg   │
│  │ +1111111111│ Send   │ 15:00 │ Mike  │ Afternoon check            │ Afternoon  │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘

🔄 EXECUTION FLOW DETAILED:

1. BACKGROUND TASK START:
   Time: Every 30 seconds
   Action: process_all_active_triggers()

2. SHEET DISCOVERY:
   Query: SELECT * FROM google_sheets WHERE status = 'ACTIVE'
   Result: List of active sheets

3. TRIGGER PROCESSING:
   For each sheet:
   - Get triggers: SELECT * FROM google_sheet_triggers WHERE sheet_id = ? AND is_enabled = true
   - For each trigger:
     * Check trigger_type
     * If "time": call should_run_time_trigger()
     * If "new_row"/"update_row": check row conditions

4. TIME TRIGGER LOGIC (should_run_time_trigger):
   ```
   current_time = datetime.utcnow()
   config = trigger.trigger_config or {}
   
   # Check for specific_times
   if 'specific_times' in config:
       specific_times = config['specific_times']
       current_time_str = current_time.strftime('%H:%M')
       if current_time_str in specific_times:
           return True
   
   # Check interval mode
   interval = config.get('interval', 3600)
   last_triggered = trigger.last_triggered_at
   
   if not last_triggered:
       return True  # Never triggered before
   
   next_run = last_triggered + timedelta(seconds=interval)
   return current_time >= next_run
   ```

5. MESSAGE EXECUTION (process_single_trigger):
   ```
   # Fetch sheet data
   rows, headers = sheets_service.get_sheet_data_with_headers()
   
   # Filter rows based on conditions
   for row in rows:
       if row['Status'] == trigger.trigger_value:
           # Build personalized message
           message = trigger.message_template
           message = message.replace('{{Name}}', row.get('Name', ''))
           message = message.replace('{{Phone}}', row.get('Phone', ''))
           
           # Send via WhatsApp API
           send_whatsapp_message(row['Phone'], message)
           
           # Update status in sheet
           update_cell(row_number, 'Status', 'Sent')
   ```

📱 WHATSAPP INTEGRATION:

1. OFFICIAL WHATSAPP API:
   - Uses OfficialMessageService
   - Requires OfficialWhatsAppConfig
   - No device dependency
   - Template-based messages

2. MESSAGE TEMPLATES:
   - Supports {{Name}}, {{Phone}}, {{Email}} placeholders
   - Can reference any column from Google Sheet
   - Personalized for each recipient

3. DELIVERY TRACKING:
   - Updates trigger history table
   - Records success/failure status
   - Logs message IDs and timestamps

📊 MONITORING AND LOGGING:

🔍 SERVER LOGS TO WATCH:
- "🕐 Processing time-based trigger {trigger_id}"
- "🚀 Time trigger {trigger_id} executing NOW"
- "✅ Time trigger {trigger_id} executed successfully"
- "📱 Sending messages via Official WhatsApp API"
- "⏰ Time trigger {trigger_id} not due yet"

📊 DATABASE TABLES TO CHECK:
- google_sheet_triggers: Trigger configurations
- sheet_trigger_history: Execution records
- google_sheets: Sheet information
- whatsapp_inbox: Sent messages

🔧 TROUBLESHOOTING GUIDE:

❌ COMMON ISSUES AND SOLUTIONS:

1. TRIGGER NOT FIRING:
   - Check: is_enabled = true
   - Check: sheet status = 'ACTIVE'
   - Check: trigger_config timing
   - Check: background task running

2. NO MESSAGES SENT:
   - Check: WhatsApp API configuration
   - Check: phone number format (+country code)
   - Check: message template validity
   - Check: Official WhatsApp Config

3. WRONG TIMING:
   - Check: execution_interval vs specific_times
   - Check: timezone differences
   - Check: last_triggered_at timestamp
   - Check: schedule_column format

4. DUPLICATE MESSAGES:
   - Check: trigger history for duplicates
   - Check: Status column updates
   - Check: multiple overlapping triggers
   - Check: background task frequency

🚀 BEST PRACTICES:

✅ DO:
- Use specific_times for exact scheduling
- Set proper execution intervals
- Monitor logs regularly
- Test with small data sets first
- Use descriptive message templates
- Keep phone numbers in international format

❌ DON'T:
- Set very short intervals (< 30 seconds)
- Use overlapping trigger conditions
- Forget to update trigger history
- Ignore error logs
- Use invalid phone number formats
- Create too many triggers at once

📈 PERFORMANCE CONSIDERATIONS:

- Background task runs every 30 seconds
- Each trigger processes all sheet rows
- Large sheets may need optimization
- Consider caching for frequent access
- Monitor database query performance

🎯 SUMMARY:

The time-based trigger system is a complete automation framework that:
1. Checks Google Sheet data regularly
2. Evaluates timing conditions
3. Sends personalized WhatsApp messages
4. Tracks execution history
5. Handles errors gracefully

It's designed for reliability, scalability, and ease of use with detailed logging and monitoring capabilities.
    """)

if __name__ == "__main__":
    explain_trigger_system()
