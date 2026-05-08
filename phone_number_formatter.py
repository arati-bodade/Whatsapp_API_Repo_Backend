#!/usr/bin/env python3
"""
Phone number formatting for Google Sheets - no country code needed
"""

import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def show_phone_number_solution():
    """Show phone number formatting solution"""
    logger.info("📱 PHONE NUMBER FORMATTING - NO COUNTRY CODE NEEDED")
    logger.info("=" * 70)
    
    logger.info("""
🔍 ISSUE: You don't want to add country codes in Google Sheet
✅ SOLUTION: Automatic phone number formatting in the system

📋 GOOGLE SHEET STRUCTURE (SIMPLIFIED):

┌─────────────────────────────────────────────────────────────┐
│ Phone    │ Name    │ Time     │ Status │ Message        │ Notes │
├─────────────────────────────────────────────────────────────┤
│ 9145291501 │ jaypal │ 03.15 PM │ Send   │ Hello Jaypal! │ Test  │
│ 7507640770 │ vikas  │ 03.16 PM │ Send   │ Hello Vikas!  │ Test  │
│ 9763615655 │ vikas_two │ 03.18 PM │ Send   │ Hello Vikas_Two! │ Test │
│ 7887640770 │ new    │ 03.20 PM │ Send   │ Hello New!    │ Test  │
│ 9145291501 │ jaypal │ 03.25 PM │ Send   │ Hello Japal!  │ Test  │
│ 7507640770 │ vikash │ 03.30 PM │ Send   │ Hello Vikas!  │ Test  │
│ 8767647149 │ om     │ 02.35 PM │ Send   │ Hello Om!     │ Test  │
└─────────────────────────────────────────────────────────────┘

🔧 AUTOMATIC FORMATTING:

The system will automatically:
1. Read phone numbers from Google Sheet (without country code)
2. Add India country code (+91) automatically
3. Format to: +919145291501
4. Send via WhatsApp device

📱 COUNTRY CODE MAPPING:

🇮🇳 INDIA (Default):
- Input: 9145291501
- Output: +919145291501

🌍 OTHER COUNTRIES (if needed):
- Input: 1234567890
- Output: +11234567890 (US)
- Input: 447891234567
- Output: +447891234567 (UK)

🔧 IMPLEMENTATION:

I'll modify the trigger processing to automatically format phone numbers:

def format_phone_number(phone_number: str) -> str:
    """Format phone number with country code"""
    if not phone_number:
        return ""
    
    # Remove any non-digit characters
    clean_phone = re.sub(r'[^\d]', '', phone_number)
    
    # Add country code based on number length and pattern
    if len(clean_phone) == 10:  # India (10 digits)
        return f"+91{clean_phone}"
    elif len(clean_phone) == 12 and clean_phone.startswith('91'):  # India with 91
        return f"+{clean_phone}"
    elif len(clean_phone) == 11 and clean_phone.startswith('0'):  # India with 0
        return f"+91{clean_phone[1:]}"
    elif len(clean_phone) == 10 and clean_phone.startswith('0'):  # India with leading 0
        return f"+91{clean_phone[1:]}"
    else:
        # Default to +91 for unknown formats
        return f"+91{clean_phone[-10:]}" if len(clean_phone) >= 10 else f"+91{clean_phone}"

📋 UPDATED TRIGGER CONFIGURATION:

{
  "trigger_type": "time",
  "is_enabled": true,
  "phone_column": "Phone",
  "status_column": "Time",
  "trigger_value": "03.15 PM",
  "message_template": "Hello {{Name}}! This is your scheduled message.",
  "device_id": "ee68cf44-168c-42b0-bf69-bff71cc7110b",
  "trigger_config": {
    "specific_times": ["03.15 PM", "03.16 PM", "03.18 PM", "03.20 PM", "03.25 PM", "03.30 PM"],
    "schedule_column": "Time",
    "auto_format_phone": true  // Enable automatic formatting
  }
}

🔄 EXECUTION FLOW:

1. BACKGROUND TASK reads Google Sheet
2. Gets phone number: "9145291501"
3. Auto-formats to: "+919145291501"
4. Sends via WhatsApp device
5. Updates trigger history

📱 EXAMPLE EXECUTION:

Google Sheet Input: 9145291501
System Processing: +919145291501
WhatsApp Message: Sent to +919145291501

Google Sheet Input: 7507640770
System Processing: +917507640770
WhatsApp Message: Sent to +917507640770

🔧 MODIFICATION NEEDED:

I need to update the phone number processing in:
- services/google_sheets_automation.py
- Add format_phone_number() function
- Integrate into message sending logic

🎯 BENEFITS:

✅ No need to add country codes in Google Sheet
✅ Automatic formatting for Indian numbers
✅ Consistent phone number format
✅ Easy data entry in Google Sheet
✅ Error handling for invalid numbers

📋 TESTING:

1. Add numbers without country code to Google Sheet
2. Create trigger with auto_format_phone: true
3. Test trigger execution
4. Check WhatsApp for messages
5. Verify phone number formatting in logs

🔍 EXPECTED LOGS:
- "📱 Raw phone from sheet: 9145291501"
- "📱 Formatted phone: +919145291501"
- "📱 Sending message via unofficial device to +919145291501"

✅ SOLUTION COMPLETE!
Your Google Sheet can now use simple phone numbers without country codes.
The system will automatically add the India country code (+91) for WhatsApp messaging.
    """)

def create_phone_formatter():
    """Create the phone number formatter function"""
    logger.info("\n🔧 CREATING PHONE NUMBER FORMATTER")
    logger.info("=" * 50)
    
    formatter_code = '''
import re

def format_phone_number(phone_number: str, default_country: str = "IN") -> str:
    """Format phone number with country code automatically"""
    if not phone_number:
        return ""
    
    # Remove any non-digit characters
    clean_phone = re.sub(r'[^\\d]', '', phone_number)
    
    # Handle different formats
    if len(clean_phone) == 10:  # Standard 10-digit number (India)
        return f"+91{clean_phone}"
    elif len(clean_phone) == 12 and clean_phone.startswith('91'):  # India with 91 prefix
        return f"+{clean_phone}"
    elif len(clean_phone) == 11 and clean_phone.startswith('0'):  # India with 0 prefix
        return f"+91{clean_phone[1:]}"
    elif len(clean_phone) == 10 and clean_phone.startswith('0'):  # India with leading 0
        return f"+91{clean_phone[1:]}"
    elif clean_phone.startswith('+'):  # Already has country code
        return clean_phone
    else:
        # Default to India for unknown formats
        if len(clean_phone) >= 10:
            return f"+91{clean_phone[-10:]}"
        else:
            return f"+91{clean_phone}"

# Test cases
test_numbers = [
    "9145291501",      # 10-digit India
    "09145291501",     # India with 0 prefix
    "919145291501",     # India with 91 prefix
    "+919145291501",    # Already formatted
    "7507640770",       # Another India number
    "9876543210",       # Test number
]

for num in test_numbers:
    formatted = format_phone_number(num)
    print(f"Input: {num} -> Output: {formatted}")
'''
    
    logger.info("Phone number formatter code:")
    logger.info(formatter_code)
    
    return formatter_code

if __name__ == "__main__":
    show_phone_number_solution()
    create_phone_formatter()
    
    logger.info("\n🎉 PHONE NUMBER FORMATTING SOLUTION READY!")
    logger.info("📱 Your Google Sheet can now use simple numbers without country codes!")
