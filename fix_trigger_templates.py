#!/usr/bin/env python3
"""
Fix trigger template_name and device connection issues
"""

import logging
from db.session import SessionLocal
from models.google_sheet import GoogleSheetTrigger

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_trigger_template_names():
    """Fix missing template_name in triggers"""
    logger.info("🔧 FIXING TRIGGER TEMPLATE NAMES")
    logger.info("=" * 70)
    
    db = SessionLocal()
    try:
        # Get all active triggers
        triggers = db.query(GoogleSheetTrigger).filter(
            GoogleSheetTrigger.is_enabled == True
        ).all()
        
        logger.info(f"📊 Found {len(triggers)} active triggers")
        
        fixed_count = 0
        
        for trigger in triggers:
            logger.info(f"⚡ Trigger: {trigger.trigger_id}")
            logger.info(f"   Current template_name: {trigger.template_name}")
            logger.info(f"   Current message_template: {trigger.message_template}")
            
            # Fix template_name
            if not trigger.template_name:
                # Use message_template as template_name
                trigger.template_name = trigger.message_template or "Default Message"
                logger.info(f"   ✅ Fixed template_name to: {trigger.template_name}")
                fixed_count += 1
            
            # Ensure message_template has content
            if not trigger.message_template:
                trigger.message_template = "Hello {Name}! {Massage}"
                logger.info(f"   ✅ Fixed message_template to: {trigger.message_template}")
                fixed_count += 1
        
        # Commit changes
        db.commit()
        
        logger.info(f"✅ Fixed {fixed_count} trigger configurations")
        
        # Verify fixes
        logger.info("\n🔍 VERIFYING FIXES")
        
        fixed_triggers = db.query(GoogleSheetTrigger).filter(
            GoogleSheetTrigger.is_enabled == True
        ).all()
        
        for trigger in fixed_triggers[:5]:  # Show first 5
            logger.info(f"⚡ Trigger: {trigger.trigger_id}")
            logger.info(f"   template_name: {trigger.template_name}")
            logger.info(f"   message_template: {trigger.message_template}")
            logger.info(f"   device_id: {trigger.device_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fix error: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def show_timing_fix():
    """Show timing fix solution"""
    logger.info("\n⏰ TIMING ISSUE FIX")
    logger.info("=" * 50)
    
    logger.info("""
🔍 TIMING ISSUES IDENTIFIED:

1️⃣ BACKGROUND TASK NOT RUNNING:
   - Server logs show "Google Sheets automation disabled"
   - Background task not processing triggers
   - SOLUTION: Enable background task

2️⃣ WRONG TIMING IN LOGS:
   - Logs show old times (11:16 AM, 12:25 PM)
   - Current time is 6:21 PM
   - SOLUTION: Restart server to fix timing

3️⃣ DEVICE CONNECTION ISSUES:
   - Device not connected to WhatsApp Engine
   - SOLUTION: Reconnect device in frontend

🔧 IMMEDIATE FIXES:

1️⃣ ENABLE BACKGROUND TASK:
   - Check main.py for background task configuration
   - Ensure Google Sheets automation is enabled
   - Restart server

2️⃣ RESTART SERVER:
   - Stop current server
   - Start fresh server
   - This fixes timing issues

3️⃣ RECONNECT DEVICE:
   - Go to WhatsApp device management
   - Disconnect device "vhgfhv"
   - Reconnect and scan QR code

4️⃣ ADD STATUS = "Send" ROWS:
   - Change some Google Sheet rows to Status = "Send"
   - This gives triggers something to process

🎯 EXPECTED RESULT AFTER FIXES:
✅ Background task runs every 30 seconds
✅ Current time shown in logs
✅ Device connected to WhatsApp Engine
✅ Triggers process Status = "Send" rows
✅ Messages sent successfully
✅ WhatsApp messages received

📱 EXPECTED LOGS AFTER FIXES:
🔄 Processing all active triggers...
🎯 Row 1: MATCH! Status 'SEND' == 'SEND'
📱 Using unofficial device 36711d22-ac2c-4e85-9b04-3f06a7d73158
📱 Sending message via unofficial device to +919145291501
✅ Message sent successfully via unofficial device to +919145291501
✅ Updated row 1 status to 'SENT'

🔍 STEP-BY-STEP SOLUTION:

STEP 1: FIX TRIGGER TEMPLATES
   - Run this script to fix template_name
   - Ensure all triggers have message_template

STEP 2: RESTART SERVER
   - Stop current server (Ctrl+C)
   - Start fresh server
   - Check for "Google Sheets automation enabled"

STEP 3: RECONNECT DEVICE
   - Go to frontend device management
   - Disconnect and reconnect device
   - Wait for successful connection

STEP 4: ADD TEST ROWS
   - Change Status = "Send" in Google Sheet
   - Wait for background task processing

STEP 5: MONITOR RESULTS
   - Check server logs for current time
   - Check WhatsApp for messages
   - Verify trigger history

🎉 SUCCESS INDICATORS:
✅ template_name fixed for all triggers
✅ Background task running with current time
✅ Device connected to WhatsApp Engine
✅ Status = "Send" rows processed
✅ Messages sent successfully
✅ WhatsApp messages received

🚀 FINAL STATUS:
After these fixes, your trigger system will work perfectly!

The timing and template issues will be resolved.
    """)

if __name__ == "__main__":
    success = fix_trigger_template_names()
    show_timing_fix()
    
    if success:
        logger.info("\n🎉 TRIGGER TEMPLATES FIXED!")
        logger.info("🚀 Restart server and reconnect device to complete fix")
    else:
        logger.info("\n❌ TRIGGER TEMPLATE FIX FAILED")
        logger.info("🔧 Check the errors above")
