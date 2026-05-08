#!/usr/bin/env python3
"""
Time-based triggers using unofficial devices (WhatsAppEngine)
"""

import logging
import asyncio
from datetime import datetime, timedelta
from db.session import SessionLocal

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

from models.google_sheet import GoogleSheet, GoogleSheetTrigger, TriggerType
from models.device import Device
from services.whatsapp_engine_service import WhatsAppEngineService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_unofficial_time_trigger():
    """Create time-based trigger using unofficial device"""
    logger.info("📱 CREATING TIME-BASED TRIGGER WITH UNOFFICIAL DEVICE")
    logger.info("=" * 60)
    
    # Your sheet ID
    sheet_id = get_default_sheet_id()
    
    db = SessionLocal()
    try:
        # Check available devices
        devices = db.query(Device).filter(
            Device.session_status == "connected"
        ).all()
        
        logger.info(f"📱 Found {len(devices)} connected devices")
        
        for device in devices:
            logger.info(f"   📱 Device: {device.device_name}")
            logger.info(f"      ID: {device.device_id}")
            logger.info(f"      Status: {device.session_status}")
        
        if not devices:
            logger.error("❌ No connected devices found!")
            logger.info("💡 Make sure at least one device is connected")
            return False
        
        # Use first connected device
        device = devices[0]
        logger.info(f"✅ Using device: {device.device_name} ({device.device_id})")
        
        # Create time trigger with device
        trigger_data = {
            "trigger_type": "time",
            "is_enabled": True,
            "phone_column": "Phone",
            "status_column": "Time",
            "trigger_value": "03.15 PM",
            "message_template": "Hello {{Name}}! This is your scheduled message.",
            "device_id": str(device.device_id),  # 🔥 KEY: Use device_id
            "execution_interval": 1800,  # Every 30 minutes
            "trigger_config": {
                "specific_times": ["03.15 PM", "03.16 PM", "03.18 PM", "03.20 PM", "03.25 PM", "03.30 PM", "02.35 PM"],
                "schedule_column": "Time"
            }
        }
        
        logger.info(f"📋 Trigger configuration:")
        logger.info(f"   Type: {trigger_data['trigger_type']}")
        logger.info(f"   Device: {device.device_name}")
        logger.info(f"   Times: {trigger_data['trigger_config']['specific_times']}")
        logger.info(f"   Interval: {trigger_data['execution_interval']} seconds")
        logger.info(f"   Message: {trigger_data['message_template']}")
        
        # Test WhatsApp engine service
        logger.info("\n🧪 TESTING WHATSAPP ENGINE SERVICE")
        try:
            whatsapp_service = WhatsAppEngineService()
            logger.info("✅ WhatsAppEngineService initialized")
            
            # Test device availability
            device_status = whatsapp_service.get_device_status(device.device_id)
            logger.info(f"📱 Device status: {device_status}")
            
        except Exception as e:
            logger.error(f"❌ WhatsApp engine error: {e}")
            logger.info("💡 Make sure WhatsAppEngineService is properly configured")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False
    finally:
        db.close()

def show_unofficial_trigger_setup():
    """Show how to set up unofficial device triggers"""
    logger.info("\n🔧 UNOFFICIAL DEVICE TRIGGER SETUP")
    logger.info("=" * 60)
    
    logger.info("""
📱 USING UNOFFICIAL DEVICES FOR TIME-BASED TRIGGERS:

🔧 TRIGGER CONFIGURATION:

{
  "trigger_type": "time",
  "is_enabled": true,
  "phone_column": "Phone",
  "status_column": "Time",
  "trigger_value": "03.15 PM",
  "message_template": "Hello {{Name}}! This is your scheduled message.",
  "device_id": "667ed3f7-c955-47d2-82b5-3d211cd75e87",  // 🔥 KEY: Device ID
  "execution_interval": 1800,
  "trigger_config": {
    "specific_times": ["03.15 PM", "03.16 PM", "03.18 PM", "03.20 PM", "03.25 PM", "03.30 PM"],
    "schedule_column": "Time"
  }
}

📋 GOOGLE SHEET STRUCTURE:

┌─────────────────────────────────────────────────────────────┐
│ Phone      │ Name    │ Time     │ Status │ Message        │ Notes │
├─────────────────────────────────────────────────────────────┤
│ +919145291501 │ jaypal │ 03.15 PM │ Send   │ Hello Jaypal! │ Test  │
│ +917507640770 │ vikas  │ 03.16 PM │ Send   │ Hello Vikas!  │ Test  │
│ +919763615655 │ vikas_two │ 03.18 PM │ Send   │ Hello Vikas_Two! │ Test │
│ +917887640770 │ new    │ 03.20 PM │ Send   │ Hello New!    │ Test  │
│ +919145291501 │ jaypal │ 03.25 PM │ Send   │ Hello Japal!  │ Test  │
│ +917507640770 │ vikash │ 03.30 PM │ Send   │ Hello Vikas!  │ Test  │
│ +918767647149 │ om     │ 02.35 PM │ Send   │ Hello Om!     │ Test  │
└─────────────────────────────────────────────────────────────┘

🔄 EXECUTION FLOW WITH UNOFFICIAL DEVICES:

1. BACKGROUND TASK (Every 30 seconds)
   ↓
2. process_all_active_triggers()
   ↓
3. process_sheet_triggers() - finds device_id
   ↓
4. should_run_time_trigger() - checks timing
   ↓
5. process_single_trigger() - uses WhatsAppEngineService
   ↓
6. whatsapp_service.send_message(device_id, phone, message)
   ↓
7. Update trigger history

📱 WHATSAPP ENGINE SERVICE:

- Uses connected WhatsApp devices
- Sends messages via WhatsAppEngineService
- Requires device to be connected
- No Official WhatsApp API needed
- Uses your existing device infrastructure

🔍 MONITORING:

Watch for these logs:
- "🕐 Processing time-based trigger {trigger_id}"
- "🚀 Time trigger {trigger_id} executing NOW"
- "📱 Sending message via WhatsAppEngineService"
- "✅ Message sent successfully"
- "❌ WhatsApp engine error"

📋 API CALL TO CREATE TRIGGER:

POST /api/google-sheets/{sheet_id}/triggers
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json

{
  "trigger_type": "time",
  "is_enabled": true,
  "phone_column": "Phone",
  "status_column": "Time",
  "trigger_value": "03.15 PM",
  "message_template": "Hello {{Name}}! This is your scheduled message.",
  "device_id": "667ed3f7-c955-47d2-82b5-3d211cd75e87",
  "execution_interval": 1800,
  "trigger_config": {
    "specific_times": ["03.15 PM", "03.16 PM", "03.18 PM", "03.20 PM", "03.25 PM", "03.30 PM"],
    "schedule_column": "Time"
  }
}

🚀 EXPECTED BEHAVIOR:

- At 03:15 PM → Sends "Hello Jaypal!" to +919145291501 via device
- At 03:16 PM → Sends "Hello Vikas!" to +917507640770 via device
- At 03:18 PM → Sends "Hello Vikas_Two!" to +919763615655 via device
- At 03:20 PM → Sends "Hello New!" to +917887640770 via device
- At 03:25 PM → Sends "Hello Japal!" to +919145291501 via device
- At 03:30 PM → Sends "Hello Vikas!" to +917507640770 via device
- At 02:35 PM → Sends "Hello Om!" to +918767647149 via device

✅ REQUIREMENTS:

1. Connected WhatsApp device
2. Valid device_id
3. WhatsAppEngineService configured
4. Google Sheet with proper structure
5. Time-based trigger with device_id

🔧 TROUBLESHOOTING:

❌ If messages not sending:
- Check device connection status
- Verify device_id is correct
- Check WhatsAppEngineService logs
- Verify trigger configuration

❌ If device not found:
- Make sure device is connected
- Check device_id format (UUID)
- Verify device exists in database

❌ If timing wrong:
- Check specific_times format
- Verify schedule_column exists
- Check timezone differences
    """)

if __name__ == "__main__":
    success = create_unofficial_time_trigger()
    show_unofficial_trigger_setup()
    
    if success:
        logger.info("\n✅ UNOFFICIAL DEVICE TRIGGER SETUP READY")
        logger.info("📱 Time triggers will use your connected WhatsApp devices!")
    else:
        logger.info("\n❌ SETUP FAILED - CHECK DEVICE CONNECTION")
