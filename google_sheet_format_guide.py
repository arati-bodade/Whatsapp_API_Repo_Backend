#!/usr/bin/env python3
"""
Complete Google Sheet format guide for triggers
"""

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def show_google_sheet_format():
    """Show complete Google Sheet format"""
    logger.info("📊 GOOGLE SHEET FORMAT GUIDE")
    logger.info("=" * 70)
    
    logger.info("""
📱 REQUIRED GOOGLE SHEET FORMAT:

🔧 COLUMN HEADERS (EXACT SPELLING):
| Phone | Name | Time | Massage | Status |
|-------|-------|-------|---------|--------|

📝 COLUMN DESCRIPTIONS:
1️⃣ Phone: Phone number (without country code)
2️⃣ Name: Recipient name (for personalization)
3️⃣ Time: Time when message should be sent (optional)
4️⃣ Massage: Message content (note: "Massage" not "Message")
5️⃣ Status: Trigger status (CRITICAL for triggers)

🔍 CURRENT GOOGLE SHEET DATA:
| Phone | Name | Time | Massage | Status |
|-------|-------|-------|---------|--------|
| 9145291501 | jaypal | 5:31:00 PM | Hello Jaypal | SENT |
| 7507640770 | vikas | 5:32:00 PM | Hello Vikas | SENT |
| 9763615655 | vikas_two | 5:34:00 PM | Hello Vikas_Two | SENT |
| 7887640770 | new | 5:36:00 PM | Hello New | SENT |
| 9145291501 | jaypal | 5:38:00 PM | Hello Japal , How are you | SENT |

🎯 WHAT YOU NEED TO ADD/CHANGE:

1️⃣ CHANGE STATUS TO "Send":
   - Change some rows from "SENT" to "Send"
   - Triggers look for Status = "Send"
   - After sending, status changes to "SENT"

2️⃣ ADD NEW ROWS WITH "Send":
   | Phone | Name | Time | Massage | Status |
   |-------|-------|-------|---------|--------|
   | 9145291501 | Test User | 6:05 PM | Test message - PLEASE SEND | Send |
   | 7507640770 | Test Vikas | 6:06 PM | Another test message | Send |

🔧 TRIGGER CONFIGURATION:
✅ All triggers now configured to:
   - Look at: Status column
   - Match value: "Send"
   - Send to: Your device (36711d22-ac2c-4e85-9b04-3f06a7d73158)

📱 PHONE NUMBER FORMAT:
✅ Use format: 9145291501 (without country code)
✅ System auto-adds: +91
✅ Final format: +919145291501

📝 MESSAGE PERSONALIZATION:
✅ Use placeholders in message:
   - {Name} → Recipient name
   - {Phone} → Phone number
   - {Time} → Time value
   - {Massage} → Message content

🔍 EXAMPLE PERSONALIZED MESSAGE:
If message template: "Hello {Name}! {Massage}"
Row data: Name="jaypal", Massage="Hello Jaypal"
Result: "Hello jaypal! Hello Jaypal"

🎯 STEP-BY-STEP SETUP:

STEP 1: OPEN GOOGLE SHEET
- URL: https://docs.google.com/spreadsheets/d/1eF28T3dsJ78IaDSVQI0T3wvCD9lQBkqHhzjgYE1mEjw

STEP 2: VERIFY COLUMNS
- Ensure you have: Phone, Name, Time, Massage, Status
- Spelling must be exact (case-sensitive)

STEP 3: ADD TEST ROWS
- Add new rows or change existing ones
- Set Status = "Send" (NOT "SENT")

STEP 4: WAIT FOR TRIGGERS
- Background task runs every 30 seconds
- Or restart server to trigger immediately

STEP 5: MONITOR RESULTS
- Check server logs
- Check WhatsApp messages
- Check Google Sheet status updates

🎉 EXPECTED WORKFLOW:
1. You add row with Status = "Send"
2. Background task finds the row
3. Phone formatted: 9145291501 → +919145291501
4. Message personalized with row data
5. Message sent via your device
6. Status updated to "SENT"
7. You receive WhatsApp message

📱 EXAMPLE COMPLETE WORKFLOW:

BEFORE:
| Phone | Name | Time | Massage | Status |
|-------|-------|-------|---------|--------|
| 9145291501 | Test User | 6:05 PM | Hello from trigger | Send |

AFTER PROCESSING:
| Phone | Name | Time | Massage | Status |
|-------|-------|-------|---------|--------|
| 9145291501 | Test User | 6:05 PM | Hello from trigger | SENT |

📱 WHAT YOU RECEIVE:
"Hello Test User! Hello from trigger"
sent to +919145291501

🔍 COMMON MISTAKES TO AVOID:

❌ WRONG COLUMN NAMES:
   - "Message" instead of "Massage"
   - "status" instead of "Status"
   - "phone" instead of "Phone"

❌ WRONG STATUS VALUES:
   - "sent" instead of "Send"
   - "SEND" instead of "Send"
   - "send" instead of "Send"

❌ WRONG PHONE FORMAT:
   - +919145291501 (with country code)
   - 91-9145291501 (with dashes)
   - 9145291501 (correct format)

🎯 FINAL STATUS:
Your Google Sheet format is correct!
Just change some Status values to "Send" and triggers will work!

🚀 READY TO USE:
1. Change Status = "Send" in some rows
2. Wait 30 seconds
3. Check WhatsApp for messages
4. Status will automatically update to "SENT"

🎉 SUCCESS INDICATORS:
✅ Correct column headers
✅ Status = "Send" values
✅ Phone numbers in correct format
✅ Message content in Massage column
✅ Triggers processing successfully
✅ WhatsApp messages received
    """)

if __name__ == "__main__":
    show_google_sheet_format()
    
    logger.info("\n📊 GOOGLE SHEET FORMAT GUIDE COMPLETE!")
    logger.info("🚀 Change Status = 'Send' and triggers will work!")
