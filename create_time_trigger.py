#!/usr/bin/env python3
"""
Create a time-based trigger for the specific Google Sheet for testing
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
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_time_trigger():
    """Create a time-based trigger for the test sheet"""
    logger.info("🔧 CREATING TIME-BASED TRIGGER FOR TESTING")
    logger.info("=" * 60)
    
    # Sheet ID from URL
    sheet_id = get_default_sheet_id()
    
    # Trigger data
    trigger_data = {
        "trigger_type": "time",
        "is_enabled": True,
        "message_template": "Test time trigger message - This should send every hour!",
        "phone_column": "Phone",
        "status_column": "Status", 
        "trigger_value": "Send",
        "execution_interval": 1800  # 30 minutes for testing
    }
    
    logger.info(f"📋 Creating trigger for sheet: {sheet_id}")
    logger.info(f"📋 Trigger data: {json.dumps(trigger_data, indent=2)}")
    
    # API call
    base_url = "http://localhost:8000"
    endpoint = f"/api/google-sheets/{sheet_id}/triggers"
    
    try:
        # Note: This would need JWT token in real usage
        response = requests.post(f"{base_url}{endpoint}", json=trigger_data, timeout=10)
        
        logger.info(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info("✅ Time-based trigger created successfully!")
            logger.info(f"📋 Trigger ID: {data.get('trigger_id')}")
            logger.info(f"📋 Device ID: {data.get('device_id')}")
            logger.info(f"📋 Created at: {data.get('created_at')}")
            logger.info(f"📋 Message template: {data.get('message_template')}")
            logger.info(f"📋 Execution interval: {trigger_data['execution_interval']} seconds")
            
            # Calculate when it will first run
            created_at = data.get('created_at')
            if created_at:
                from datetime import timedelta
                first_run = datetime.strptime(created_at.replace('Z', '+00:00'), "%Y-%m-%dT%H:%M:%S.%f") + timedelta(seconds=trigger_data['execution_interval'])
                logger.info(f"⏰ First execution expected at: {first_run}")
            
            return True
        else:
            logger.error(f"❌ Failed to create trigger: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error creating trigger: {e}")
        return False

def show_monitoring_guide():
    """Show how to monitor the new time trigger"""
    logger.info("\n📋 MONITORING GUIDE FOR NEW TIME TRIGGER")
    logger.info("=" * 60)
    
    logger.info(f"""
🕐 NEW TIME TRIGGER DETAILS:
- Trigger ID: Will be shown in response above
- Execution Interval: 1800 seconds (30 minutes)
- Message: "Test time trigger message - This should send every hour!"
- Target: Send messages when Status column contains "Send"

🔍 TO VERIFY IT'S WORKING:

1. SERVER LOGS:
   Look for: "🕐 Processing time-based trigger {trigger_id}"
   Look for: "🚀 Time trigger {trigger_id} executing NOW"
   Look for: "✅ Time trigger {trigger_id} executed successfully"

2. EXPECTED TIMELINE:
   Now: {datetime.now()}
   First execution: Now + 30 minutes
   Second execution: Now + 60 minutes
   Third execution: Now + 90 minutes
   etc.

3. MESSAGE RECEIPT:
   Check WhatsApp for received messages
   Check trigger history in database

📱 BACKGROUND TASK:
Should be polling every 30 seconds and processing time triggers
Look for logs: "🔄 LEGACY PROCESSING: Processing triggers"

⚠️  IF NOT WORKING:
1. Check if trigger was created successfully (response 200)
2. Check if background task is running
3. Check server logs for execution attempts
4. Verify trigger_config has correct interval
5. Check sheet data has 'Status' column with 'Send' values
    """)

if __name__ == "__main__":
    success = create_time_trigger()
    show_monitoring_guide()
    
    if success:
        logger.info("\n✅ TIME TRIGGER CREATION COMPLETED")
        logger.info("🚀 Monitor logs for execution in 30 minutes!")
    else:
        logger.info("\n❌ TIME TRIGGER CREATION FAILED")
