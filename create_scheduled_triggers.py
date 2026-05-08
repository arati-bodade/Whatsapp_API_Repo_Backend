#!/usr/bin/env python3
"""
Create time-based triggers with your exact schedule
"""

import logging

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

import requests
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_scheduled_triggers():
    """Create time-based triggers with your exact schedule"""
    logger.info("⏰ CREATING YOUR SCHEDULED TRIGGERS")
    logger.info("=" * 60)
    
    # Your Google Sheet ID
    sheet_id = get_default_sheet_id()
    
    # Your exact schedule data
    schedule_data = [
        {
            "name": "Morning Message",
            "time": "09:15",
            "message": "Hello Jaypal! Good morning!",
            "recipient": "+919145291501"  # Jaypal's number
        },
        {
            "name": "Lunch Reminder", 
            "time": "12:00",
            "message": "Hello Vikas! Don't forget lunch!",
            "recipient": "+917507640770"  # Vikas's number
        },
        {
            "name": "Evening Greeting",
            "time": "15:00",
            "message": "Hello Vikas_Two! Good evening!",
            "recipient": "+917887640770"  # Vikas_Two's number
        },
        {
            "name": "New Customer Welcome",
            "time": "03:20 PM",
            "message": "Hello New! Welcome to our service!",
            "recipient": "+917887647149"  # New's number
        },
        {
            "name": "How Are You Query",
            "time": "02:35 PM",
            "message": "Hello Om! How are you doing?",
            "recipient": "+918767647149"  # Om's number
        }
    ]
    
    base_url = "http://localhost:8000"
    
    logger.info(f"📋 Creating {len(schedule_data)} scheduled triggers")
    
    for i, trigger_info in enumerate(schedule_data):
        logger.info(f"\n{i+1}. 📅 {trigger_info['name']}")
        logger.info(f"   Time: {trigger_info['time']}")
        logger.info(f"   Message: {trigger_info['message']}")
        logger.info(f"   Recipient: {trigger_info['recipient']}")
        
        # Create trigger data
        trigger_data = {
            "trigger_type": "time",
            "is_enabled": True,
            "phone_column": "Phone",
            "status_column": "Time",
            "trigger_value": trigger_info['time'],
            "message_template": trigger_info['message'],
            "execution_interval": 3600,  # Check daily
            "specific_times": [trigger_info['time']]  # Use specific time
        }
        
        logger.info(f"   📋 Trigger data: {json.dumps(trigger_data, indent=2)}")
        
        # Create the trigger
        try:
            response = requests.post(
                f"{base_url}/api/google-sheets/{sheet_id}/triggers",
                json=trigger_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"   ✅ Created: {data.get('trigger_id')}")
                logger.info(f"   📱 Device ID: {data.get('device_id')}")
                logger.info(f"   🕐 Created at: {data.get('created_at')}")
            else:
                logger.error(f"   ❌ Failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"   ❌ Error: {e}")
    
    logger.info("\n✅ SCHEDULED TRIGGERS CREATED")
    logger.info(f"🕐 EXPECTED EXECUTION TIMES:")
    for trigger_info in schedule_data:
        logger.info(f"   📅 {trigger_info['time']} - {trigger_info['message']}")
    
    logger.info("\n📋 NEXT STEPS:")
    logger.info("1. Monitor server logs for execution")
    logger.info("2. Check WhatsApp for received messages") 
    logger.info("3. Verify trigger history in database")
    logger.info("4. Add more scheduled times as needed")
    
    logger.info("\n🚀 YOUR SCHEDULE IS READY!")
    logger.info("The system will send messages at your specified times automatically.")

if __name__ == "__main__":
    create_scheduled_triggers()
