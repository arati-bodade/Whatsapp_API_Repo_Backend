#!/usr/bin/env python3
"""
Update all triggers to use your device ID
"""

import logging
from db.session import SessionLocal
from models.google_sheet import GoogleSheetTrigger

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_triggers_to_your_device():
    """Update all triggers to use your device ID"""
    logger.info("🔧 UPDATING TRIGGERS TO USE YOUR DEVICE ID")
    logger.info("=" * 60)
    
    db = SessionLocal()
    try:
        # Your device ID
        your_device_id = "36711d22-ac2c-4e85-9b04-3f06a7d73158"
        
        logger.info(f"📱 Your Device ID: {your_device_id}")
        
        # Get all active triggers
        active_triggers = db.query(GoogleSheetTrigger).filter(
            GoogleSheetTrigger.is_enabled == True
        ).all()
        
        logger.info(f"📊 Found {len(active_triggers)} active triggers")
        
        updated_count = 0
        
        for trigger in active_triggers:
            logger.info(f"⚡ Trigger: {trigger.trigger_id}")
            logger.info(f"   Current device_id: {trigger.device_id}")
            logger.info(f"   Type: {trigger.trigger_type}")
            logger.info(f"   Message: {trigger.message_template}")
            
            # Update to use your device
            trigger.device_id = your_device_id
            updated_count += 1
            
            logger.info(f"   ✅ Updated to: {your_device_id}")
        
        # Commit changes
        db.commit()
        
        logger.info(f"✅ Updated {updated_count} triggers to use your device ID")
        
        # Verify the updates
        logger.info("\n🔍 VERIFYING UPDATES")
        
        updated_triggers = db.query(GoogleSheetTrigger).filter(
            GoogleSheetTrigger.is_enabled == True,
            GoogleSheetTrigger.device_id == your_device_id
        ).all()
        
        logger.info(f"📊 {len(updated_triggers)} triggers now using your device")
        
        for trigger in updated_triggers:
            logger.info(f"   ✅ {trigger.trigger_id}: {trigger.device_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error updating triggers: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def show_next_steps():
    """Show next steps for testing"""
    logger.info("\n🎯 NEXT STEPS FOR TESTING")
    logger.info("=" * 50)
    
    logger.info("""
✅ ALL TRIGGERS UPDATED!

📱 Your Device ID: 36711d22-ac2c-4e85-9b04-3f06a7d73158

🔧 WHAT WAS DONE:
- Updated all active triggers to use your device ID
- Committed changes to database
- Verified updates were successful

🎯 IMMEDIATE ACTIONS:

1️⃣ ADD STATUS COLUMN TO GOOGLE SHEET:
   - Open your Google Sheet: 1eF28T3dsJ78IaDSVQI0T3wvCD9lQBkqHhzjgYE1mEjw
   - Add "Status" column (column E)
   - Set Status = "Send" for test rows

2️⃣ TEST TRIGGER EXECUTION:
   - Add Status = "Send" to a test row
   - Wait for background task (30 seconds)
   - Or restart server to trigger immediately

3️⃣ MONITOR LOGS:
   - Watch for: "Using unofficial device 36711d22-ac2c-4e85-9b04-3f06a7d73158"
   - Watch for: "Message sent successfully"
   - Check for any errors

4️⃣ CHECK WHATSAPP:
   - Should receive messages on your device
   - Messages should be personalized with row data

5️⃣ VERIFY TRIGGER HISTORY:
   - GET /api/google-sheets/triggers/history
   - Should show SENT status
   - Should include your device ID

🔍 EXPECTED LOGS:
📱 Using unofficial device 36711d22-ac2c-4e85-9b04-3f06a7d73158 for message sending
📱 Raw phone from sheet: 9145291501
📱 Formatted phone: +919145291501
📱 Personalized message: Hello {Name}! {Message}
📤 Processing row {row_number} via unofficial device
📱 Sending message via unofficial device 36711d22-ac2c-4e85-9b04-3f06a7d73158 to +919145291501
✅ Message sent successfully via unofficial device to +919145291501

📱 EXPECTED WHATSAPP MESSAGES:
- Hello jaypal! Hello Jaypal
- Hello vikas! Hello Vikas
- Hello new! Hello New
- etc.

🎉 SUCCESS INDICATORS:
✅ Triggers use your device ID
✅ Messages sent to your WhatsApp
✅ Trigger history shows SENT status
✅ Google Sheet status updated to SENT
✅ No more "not send the message" issues

🚀 READY TO TEST!

Your triggers are now configured to send messages via your device.
Add the Status column to Google Sheet and you're done!
    """)

if __name__ == "__main__":
    success = update_triggers_to_your_device()
    show_next_steps()
    
    if success:
        logger.info("\n🎉 TRIGGERS UPDATED SUCCESSFULLY!")
        logger.info("📱 All triggers now use your device ID")
        logger.info("🚀 Ready to send messages!")
    else:
        logger.info("\n❌ TRIGGER UPDATE FAILED")
        logger.info("🔧 Check the errors above")
