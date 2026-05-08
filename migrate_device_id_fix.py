#!/usr/bin/env python3
"""
Database migration to fix Google Sheet triggers device_id constraint
"""

import logging
from sqlalchemy import text
from db.session import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_device_id_nullable():
    """Make device_id column nullable in google_sheet_triggers table"""
    db = SessionLocal()
    try:
        logger.info("🔧 MIGRATING: Making device_id nullable in google_sheet_triggers")
        logger.info("=" * 60)
        
        # Check if the column exists and its current constraint
        check_sql = """
        SELECT 
            column_name, 
            is_nullable,
            column_default
        FROM information_schema.columns 
        WHERE table_name = 'google_sheet_triggers' 
        AND column_name = 'device_id';
        """
        
        result = db.execute(text(check_sql)).fetchone()
        
        if result:
            logger.info(f"📋 Current device_id column info:")
            logger.info(f"   Column: {result[0]}")
            logger.info(f"   Nullable: {result[1]}")
            logger.info(f"   Default: {result[2]}")
            
            if result[1] == 'NO':
                logger.info("🔨 Making device_id column nullable...")
                
                # Make the column nullable
                alter_sql = """
                ALTER TABLE google_sheet_triggers 
                ALTER COLUMN device_id DROP NOT NULL;
                """
                
                db.execute(text(alter_sql))
                db.commit()
                
                logger.info("✅ device_id column is now nullable!")
                
                # Verify the change
                verify_result = db.execute(text(check_sql)).fetchone()
                logger.info(f"📋 Updated device_id column info:")
                logger.info(f"   Column: {verify_result[0]}")
                logger.info(f"   Nullable: {verify_result[1]}")
                logger.info(f"   Default: {verify_result[2]}")
                
            else:
                logger.info("✅ device_id column is already nullable!")
        else:
            logger.warning("⚠️  device_id column not found in google_sheet_triggers table")
        
        # Check existing triggers that might have NULL device_id
        check_triggers_sql = """
        SELECT COUNT(*) as total_triggers,
               COUNT(device_id) as triggers_with_device_id,
               COUNT(*) - COUNT(device_id) as triggers_without_device_id
        FROM google_sheet_triggers;
        """
        
        trigger_stats = db.execute(text(check_triggers_sql)).fetchone()
        
        logger.info(f"\n📊 Trigger statistics:")
        logger.info(f"   Total triggers: {trigger_stats[0]}")
        logger.info(f"   With device_id: {trigger_stats[1]}")
        logger.info(f"   Without device_id: {trigger_stats[2]}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def verify_fix():
    """Verify that trigger creation now works"""
    logger.info("\n🧪 VERIFYING: Trigger creation should now work")
    logger.info("=" * 60)
    
    try:
        # Test creating a trigger with device_id=None
        from models.google_sheet import GoogleSheetTrigger
        from models.busi_user import BusiUser
        import uuid
        
        db = SessionLocal()
        
        # Get a test user and sheet
        user = db.query(BusiUser).first()
        if not user:
            logger.warning("⚠️  No test user found")
            return False
        
        # Check if user has sheets
        from models.google_sheet import GoogleSheet
        sheet = db.query(GoogleSheet).filter(GoogleSheet.user_id == user.busi_user_id).first()
        
        if not sheet:
            logger.warning("⚠️  No test sheet found")
            return False
        
        logger.info(f"📋 Testing with user: {user.busi_user_id}")
        logger.info(f"📋 Testing with sheet: {sheet.sheet_name}")
        
        # Create a test trigger
        test_trigger = GoogleSheetTrigger(
            trigger_id=str(uuid.uuid4()),
            sheet_id=sheet.id,
            device_id=None,  # This should work now
            trigger_type="time",
            is_enabled=True,
            phone_column="Phone",
            status_column="Status",
            trigger_value="Send",
            message_template="Test message"
        )
        
        db.add(test_trigger)
        db.commit()
        db.refresh(test_trigger)
        
        logger.info("✅ Test trigger created successfully!")
        logger.info(f"   Trigger ID: {test_trigger.trigger_id}")
        logger.info(f"   Device ID: {test_trigger.device_id}")
        logger.info(f"   Sheet ID: {test_trigger.sheet_id}")
        
        # Clean up test trigger
        db.delete(test_trigger)
        db.commit()
        
        logger.info("🧹 Test trigger cleaned up")
        return True
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = migrate_device_id_nullable()
    
    if success:
        verify_success = verify_fix()
        
        if verify_success:
            logger.info("\n✅ MIGRATION COMPLETED SUCCESSFULLY!")
            logger.info("🚀 Google Sheet trigger creation should now work!")
        else:
            logger.error("\n❌ Migration succeeded but verification failed")
    else:
        logger.error("\n❌ Migration failed")
