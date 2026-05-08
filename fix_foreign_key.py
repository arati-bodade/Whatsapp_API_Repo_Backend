#!/usr/bin/env python3
"""
Fix foreign key constraint to point to correct table
"""

import logging
from sqlalchemy import text
from db.session import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_foreign_key_constraint():
    """Fix foreign key to point to google_sheets instead of google_sheets_v2"""
    db = SessionLocal()
    try:
        logger.info("🔧 FIXING FOREIGN KEY CONSTRAINT")
        logger.info("=" * 60)
        
        # Check current constraint
        check_constraint_sql = """
        SELECT 
            tc.constraint_name,
            tc.table_name, 
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name 
        FROM information_schema.table_constraints AS tc 
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY' 
        AND tc.table_name = 'google_sheet_triggers'
        AND kcu.column_name = 'sheet_id';
        """
        
        constraint = db.execute(text(check_constraint_sql)).fetchone()
        
        if constraint:
            logger.info("📋 Current foreign key constraint:")
            logger.info(f"   Constraint: {constraint[0]}")
            logger.info(f"   Table: {constraint[1]}.{constraint[2]}")
            logger.info(f"   References: {constraint[3]}.{constraint[4]}")
            
            if constraint[3] == 'google_sheets_v2':
                logger.info("🔨 Fix needed: Points to wrong table")
                
                # Drop the existing constraint
                drop_constraint_sql = """
                ALTER TABLE google_sheet_triggers 
                DROP CONSTRAINT google_sheet_triggers_sheet_id_fkey;
                """
                
                logger.info("🗑️  Dropping existing constraint...")
                db.execute(text(drop_constraint_sql))
                
                # Create new constraint pointing to correct table
                add_constraint_sql = """
                ALTER TABLE google_sheet_triggers 
                ADD CONSTRAINT google_sheet_triggers_sheet_id_fkey 
                FOREIGN KEY (sheet_id) 
                REFERENCES google_sheets(id) 
                ON DELETE CASCADE;
                """
                
                logger.info("➕ Adding new constraint to google_sheets table...")
                db.execute(text(add_constraint_sql))
                db.commit()
                
                logger.info("✅ Foreign key constraint fixed!")
                
                # Verify the fix
                verify_constraint = db.execute(text(check_constraint_sql)).fetchone()
                logger.info("📋 Updated foreign key constraint:")
                logger.info(f"   Constraint: {verify_constraint[0]}")
                logger.info(f"   Table: {verify_constraint[1]}.{verify_constraint[2]}")
                logger.info(f"   References: {verify_constraint[3]}.{verify_constraint[4]}")
                
            else:
                logger.info("✅ Foreign key constraint already correct")
        else:
            logger.warning("⚠️  No foreign key constraint found on sheet_id")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error fixing foreign key: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def verify_trigger_creation():
    """Verify that trigger creation now works"""
    logger.info("\n🧪 VERIFYING TRIGGER CREATION")
    logger.info("=" * 60)
    
    db = SessionLocal()
    try:
        # Get the problematic sheet ID
        sheet_id = "b9a9f439-6e73-4ab4-b9cf-12b64f2c4893"
        
        # Check if sheet exists
        check_sheet_sql = """
        SELECT id, sheet_name, user_id 
        FROM google_sheets 
        WHERE id = :sheet_id;
        """
        
        sheet = db.execute(text(check_sheet_sql), {"sheet_id": sheet_id}).fetchone()
        
        if sheet:
            logger.info("✅ Sheet found in google_sheets table:")
            logger.info(f"   ID: {sheet[0]}")
            logger.info(f"   Name: {sheet[1]}")
            logger.info(f"   User ID: {sheet[2]}")
            
            # Test creating a trigger
            test_trigger_sql = """
            INSERT INTO google_sheet_triggers (
                trigger_id, sheet_id, device_id, trigger_type, is_enabled, 
                last_triggered_at, created_at, last_processed_row, phone_column, 
                status_column, trigger_value, message_template, trigger_column, 
                webhook_url, trigger_config
            ) VALUES (
                :trigger_id, :sheet_id, :device_id, :trigger_type, :is_enabled,
                :last_triggered_at, :created_at, :last_processed_row, :phone_column,
                :status_column, :trigger_value, :message_template, :trigger_column,
                :webhook_url, :trigger_config
            );
            """
            
            import uuid
            from datetime import datetime
            
            test_params = {
                "trigger_id": str(uuid.uuid4()),
                "sheet_id": sheet_id,
                "device_id": None,
                "trigger_type": "time",
                "is_enabled": True,
                "last_triggered_at": None,
                "created_at": datetime.utcnow(),
                "last_processed_row": 0,
                "phone_column": "Phone",
                "status_column": "Status",
                "trigger_value": "Send",
                "message_template": "Test message",
                "trigger_column": None,
                "webhook_url": None,
                "trigger_config": "{}"
            }
            
            logger.info("🧪 Testing trigger creation...")
            db.execute(text(test_trigger_sql), test_params)
            db.commit()
            
            logger.info("✅ Trigger creation successful!")
            
            # Clean up test trigger
            delete_trigger_sql = """
            DELETE FROM google_sheet_triggers 
            WHERE trigger_id = :trigger_id;
            """
            
            db.execute(text(delete_trigger_sql), {"trigger_id": test_params["trigger_id"]})
            db.commit()
            
            logger.info("🧹 Test trigger cleaned up")
            
        else:
            logger.error("❌ Sheet not found in google_sheets table")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = fix_foreign_key_constraint()
    
    if success:
        verify_success = verify_trigger_creation()
        
        if verify_success:
            logger.info("\n✅ FOREIGN KEY FIX COMPLETED!")
            logger.info("🚀 Google Sheets trigger creation should now work!")
        else:
            logger.error("\n❌ Foreign key fix succeeded but verification failed")
    else:
        logger.error("\n❌ Foreign key fix failed")
