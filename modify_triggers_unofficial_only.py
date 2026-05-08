#!/usr/bin/env python3
"""
Script to modify all triggers to use only unofficial WhatsApp API
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
import logging

# Database URL
DATABASE_URL = "postgresql://whatsapp_platform_fn0k_user:AbHezwfAs553dVCy33wfHzsGMVJbf8M0@dpg-d6oh8tfafjfc7386oii0-a.oregon-postgres.render.com/whatsapp_platform_fn0k"

# Create engine
engine = create_engine(DATABASE_URL)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def modify_triggers_to_unofficial_only():
    """Modify all triggers to use only unofficial WhatsApp API"""
    
    logger.info("🔧 MODIFYING TRIGGERS TO USE ONLY UNOFFICIAL WHATSAPP API")
    logger.info("=" * 60)
    
    try:
        with engine.connect() as conn:
            
            # Step 1: Remove all official template trigger configurations
            logger.info("📋 Step 1: Removing official template configurations...")
            
            # Clear trigger_config for all triggers (removes official template settings)
            result = conn.execute(text("""
                UPDATE google_sheet_triggers 
                SET trigger_config = NULL,
                    message_template = COALESCE(message_template, 'Hello {name}')
                WHERE trigger_config IS NOT NULL
            """))
            logger.info(f"   ✅ Cleared official template configs for {result.rowcount} triggers")
            
            # Step 2: Ensure all triggers have message_template set
            logger.info("📋 Step 2: Setting default message templates...")
            
            result = conn.execute(text("""
                UPDATE google_sheet_triggers 
                SET message_template = 'Hello {name}, your message is ready!'
                WHERE message_template IS NULL OR message_template = ''
            """))
            logger.info(f"   ✅ Set default message template for {result.rowcount} triggers")
            
            # Step 3: Get triggers without device_id and set them to use first available device
            logger.info("📋 Step 3: Assigning devices to triggers without device_id...")
            
            # First, get available unofficial devices
            devices_result = conn.execute(text("""
                SELECT device_id, busi_user_id, device_name, session_status
                FROM devices 
                WHERE session_status = 'connected' 
                ORDER BY created_at DESC
            """))
            devices = devices_result.fetchall()
            
            if not devices:
                logger.warning("   ⚠️  No connected devices found. Triggers without device_id will not work.")
            else:
                logger.info(f"   📱 Found {len(devices)} connected devices")
                
                # Get triggers without device_id
                triggers_result = conn.execute(text("""
                    SELECT trigger_id, sheet_id, user_id
                    FROM google_sheet_triggers t
                    JOIN google_sheets s ON t.sheet_id = s.id
                    WHERE t.device_id IS NULL
                """))
                triggers_without_device = triggers_result.fetchall()
                
                logger.info(f"   🎯 Found {len(triggers_without_device)} triggers without device_id")
                
                # Assign devices to triggers
                for trigger in triggers_without_device:
                    trigger_id = str(trigger[0])  # Convert to string
                    user_id = trigger[2]
                    
                    # Find device for this user
                    user_device = None
                    for device in devices:
                        if device[1] == user_id:  # busi_user_id matches
                            user_device = device
                            break
                    
                    if user_device:
                        result = conn.execute(text("""
                            UPDATE google_sheet_triggers 
                            SET device_id = :device_id
                            WHERE trigger_id = :trigger_id
                        """), {
                            'device_id': user_device[0],
                            'trigger_id': trigger_id
                        })
                        logger.info(f"   ✅ Assigned device {user_device[2]} ({str(user_device[0])[:8]}...) to trigger {trigger_id}")
                    else:
                        logger.warning(f"   ⚠️  No connected device found for user {user_id}, trigger {trigger_id}")
            
            # Step 4: Commit all changes
            conn.commit()
            logger.info("   ✅ All changes committed to database")
            
            # Step 5: Verify the changes
            logger.info("📋 Step 4: Verifying changes...")
            
            # Count triggers with device_id vs without
            stats_result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total_triggers,
                    COUNT(CASE WHEN device_id IS NOT NULL THEN 1 END) as with_device_id,
                    COUNT(CASE WHEN device_id IS NULL THEN 1 END) as without_device_id,
                    COUNT(CASE WHEN trigger_config IS NOT NULL THEN 1 END) as with_official_config
                FROM google_sheet_triggers
            """))
            stats = stats_result.fetchone()
            
            logger.info(f"   📊 Trigger Statistics:")
            logger.info(f"      Total triggers: {stats[0]}")
            logger.info(f"      With device_id: {stats[1]}")
            logger.info(f"      Without device_id: {stats[2]}")
            logger.info(f"      With official config: {stats[3]}")
            
            # Show sample triggers
            sample_result = conn.execute(text("""
                SELECT 
                    t.trigger_id,
                    t.device_id IS NOT NULL as has_device,
                    t.trigger_config IS NOT NULL as has_official_config,
                    t.message_template
                FROM google_sheet_triggers t
                LIMIT 5
            """))
            samples = sample_result.fetchall()
            
            logger.info(f"   📋 Sample triggers:")
            for sample in samples:
                trigger_id, has_device, has_official, template = sample
                logger.info(f"      {trigger_id}: device={has_device}, official={has_official}, template='{template[:50]}...'")
            
            logger.info("")
            logger.info("🎉 TRIGGER MODIFICATION COMPLETED!")
            logger.info("✅ All triggers now configured for unofficial WhatsApp API only")
            logger.info("✅ Official template configurations removed")
            logger.info("✅ Message templates set for all triggers")
            logger.info("✅ Devices assigned to triggers where possible")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Error modifying triggers: {e}")
        return False

def main():
    """Main function"""
    success = modify_triggers_to_unofficial_only()
    
    if success:
        logger.info("")
        logger.info("📝 NEXT STEPS:")
        logger.info("1. Restart the backend to apply changes")
        logger.info("2. Test trigger execution with unofficial devices")
        logger.info("3. Verify triggers are working via API endpoints")
        logger.info("4. Monitor trigger history for successful message sending")
    else:
        logger.error("❌ Failed to modify triggers - please check the error above")

if __name__ == "__main__":
    main()
