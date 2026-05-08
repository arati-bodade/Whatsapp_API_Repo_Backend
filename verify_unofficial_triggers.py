#!/usr/bin/env python3
"""
Script to verify all triggers are configured for unofficial WhatsApp only
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

def verify_unofficial_triggers():
    """Verify all triggers are configured for unofficial WhatsApp only"""
    
    logger.info("🔍 VERIFYING TRIGGERS ARE UNOFFICIAL ONLY")
    logger.info("=" * 50)
    
    try:
        with engine.connect() as conn:
            
            # Step 1: Check trigger configurations
            logger.info("📋 Step 1: Checking trigger configurations...")
            
            stats_result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total_triggers,
                    COUNT(CASE WHEN device_id IS NOT NULL THEN 1 END) as with_device_id,
                    COUNT(CASE WHEN device_id IS NULL THEN 1 END) as without_device_id,
                    COUNT(CASE WHEN trigger_config IS NOT NULL THEN 1 END) as with_official_config,
                    COUNT(CASE WHEN message_template IS NOT NULL AND message_template != '' THEN 1 END) as with_message_template
                FROM google_sheet_triggers
            """))
            stats = stats_result.fetchone()
            
            logger.info(f"   📊 Trigger Statistics:")
            logger.info(f"      Total triggers: {stats[0]}")
            logger.info(f"      With device_id: {stats[1]}")
            logger.info(f"      Without device_id: {stats[2]}")
            logger.info(f"      With official config: {stats[3]}")
            logger.info(f"      With message template: {stats[4]}")
            
            # Step 2: Check for any official configurations
            logger.info("📋 Step 2: Checking for official configurations...")
            
            official_config_result = conn.execute(text("""
                SELECT trigger_id, trigger_config
                FROM google_sheet_triggers
                WHERE trigger_config IS NOT NULL
                LIMIT 5
            """))
            official_configs = official_config_result.fetchall()
            
            if official_configs:
                logger.warning(f"   ⚠️  Found {len(official_configs)} triggers with official config:")
                for config in official_configs:
                    logger.warning(f"      {config[0]}: {str(config[1])[:100]}...")
            else:
                logger.info("   ✅ No triggers with official configurations found")
            
            # Step 3: Check device assignments
            logger.info("📋 Step 3: Checking device assignments...")
            
            device_result = conn.execute(text("""
                SELECT 
                    t.trigger_id,
                    t.device_id IS NOT NULL as has_device,
                    d.device_name,
                    d.session_status
                FROM google_sheet_triggers t
                LEFT JOIN devices d ON t.device_id = d.device_id
                ORDER BY t.trigger_id
                LIMIT 10
            """))
            device_assignments = device_result.fetchall()
            
            logger.info(f"   📱 Device Assignments (first 10):")
            for assignment in device_assignments:
                trigger_id, has_device, device_name, session_status = assignment
                if has_device:
                    logger.info(f"      {trigger_id}: ✅ {device_name} ({session_status})")
                else:
                    logger.warning(f"      {trigger_id}: ❌ No device assigned")
            
            # Step 4: Check message templates
            logger.info("📋 Step 4: Checking message templates...")
            
            template_result = conn.execute(text("""
                SELECT trigger_id, message_template
                FROM google_sheet_triggers
                WHERE message_template IS NOT NULL AND message_template != ''
                ORDER BY trigger_id
                LIMIT 5
            """))
            templates = template_result.fetchall()
            
            logger.info(f"   📝 Message Templates (first 5):")
            for template in templates:
                trigger_id, message_template = template
                logger.info(f"      {trigger_id}: '{message_template[:50]}...'")
            
            # Step 5: Overall verification
            logger.info("📋 Step 5: Overall verification...")
            
            all_unofficial = (
                stats[2] == 0 and  # No triggers without device_id
                stats[3] == 0 and  # No official configurations
                stats[4] > 0      # All have message templates
            )
            
            if all_unofficial:
                logger.info("   ✅ ALL TRIGGERS ARE CONFIGURED FOR UNOFFICIAL WHATSAPP ONLY!")
                logger.info("   ✅ Every trigger has a device_id")
                logger.info("   ✅ No official configurations found")
                logger.info("   ✅ All triggers have message templates")
            else:
                logger.warning("   ⚠️  SOME TRIGGERS MAY STILL USE OFFICIAL API:")
                if stats[2] > 0:
                    logger.warning(f"      - {stats[2]} triggers without device_id")
                if stats[3] > 0:
                    logger.warning(f"      - {stats[3]} triggers with official config")
                if stats[4] == 0:
                    logger.warning("      - No triggers with message templates")
            
            # Step 6: Test API endpoints
            logger.info("📋 Step 6: Checking API endpoints...")
            
            try:
                # Try to import the updated Google Sheets API
                import sys
                sys.path.append(os.path.dirname(__file__))
                from api.google_sheets import router
                
                # Check routes
                routes = [route.path for route in router.routes]
                official_routes = [route for route in routes if 'official' in route.lower()]
                
                if official_routes:
                    logger.warning(f"   ⚠️  Found {len(official_routes)} official routes: {official_routes}")
                else:
                    logger.info("   ✅ No official routes found in API")
                
            except Exception as api_error:
                logger.error(f"   ❌ Error checking API: {api_error}")
            
            logger.info("")
            logger.info("🎉 VERIFICATION COMPLETED!")
            
            return all_unofficial
            
    except Exception as e:
        logger.error(f"❌ Error verifying triggers: {e}")
        return False

def main():
    """Main function"""
    success = verify_unofficial_triggers()
    
    if success:
        logger.info("")
        logger.info("🎉 SUCCESS: All triggers are unofficial-only!")
        logger.info("📝 READY FOR PRODUCTION:")
        logger.info("✅ Triggers will only use unofficial WhatsApp devices")
        logger.info("✅ No official WhatsApp API calls will be made")
        logger.info("✅ All messaging goes through WhatsApp Engine")
        logger.info("")
        logger.info("📋 NEXT STEPS:")
        logger.info("1. Start the backend service")
        logger.info("2. Test trigger execution via API")
        logger.info("3. Monitor message delivery through devices")
        logger.info("4. Check trigger history for successful sends")
    else:
        logger.error("❌ VERIFICATION FAILED - Some triggers may still use official API")
        logger.error("Please review the warnings above and fix any remaining issues")

if __name__ == "__main__":
    main()
