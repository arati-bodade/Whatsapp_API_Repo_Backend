#!/usr/bin/env python3
"""
Check and fix data type mismatch in foreign key
"""

import logging
from sqlalchemy import text
from db.session import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_column_types():
    """Check data types of the columns involved in foreign key"""
    db = SessionLocal()
    try:
        logger.info("🔍 CHECKING COLUMN DATA TYPES")
        logger.info("=" * 60)
        
        # Check google_sheet_triggers.sheet_id type
        check_triggers_sql = """
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns 
        WHERE table_name = 'google_sheet_triggers' 
        AND column_name = 'sheet_id';
        """
        
        trigger_col = db.execute(text(check_triggers_sql)).fetchone()
        
        if trigger_col:
            logger.info("📋 google_sheet_triggers.sheet_id:")
            logger.info(f"   Data Type: {trigger_col[1]}")
            logger.info(f"   Max Length: {trigger_col[2]}")
        
        # Check google_sheets.id type
        check_sheets_sql = """
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns 
        WHERE table_name = 'google_sheets' 
        AND column_name = 'id';
        """
        
        sheet_col = db.execute(text(check_sheets_sql)).fetchone()
        
        if sheet_col:
            logger.info("📋 google_sheets.id:")
            logger.info(f"   Data Type: {sheet_col[1]}")
            logger.info(f"   Max Length: {sheet_col[2]}")
        
        # Check google_sheets_v2.id type (the referenced table)
        check_sheets_v2_sql = """
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns 
        WHERE table_name = 'google_sheets_v2' 
        AND column_name = 'id';
        """
        
        try:
            sheet_v2_col = db.execute(text(check_sheets_v2_sql)).fetchone()
            
            if sheet_v2_col:
                logger.info("📋 google_sheets_v2.id:")
                logger.info(f"   Data Type: {sheet_v2_col[1]}")
                logger.info(f"   Max Length: {sheet_v2_col[2]}")
        except Exception as e:
            logger.info(f"📋 google_sheets_v2 table doesn't exist: {e}")
        
        return {
            "trigger_sheet_id": trigger_col,
            "sheets_id": sheet_col,
            "sheets_v2_id": sheet_v2_col if 'sheet_v2_col' in locals() else None
        }
        
    except Exception as e:
        logger.error(f"❌ Error checking column types: {e}")
        return None
    finally:
        db.close()

def fix_data_type_mismatch():
    """Fix the data type mismatch by converting sheet_id to UUID"""
    db = SessionLocal()
    try:
        logger.info("\n🔧 FIXING DATA TYPE MISMATCH")
        logger.info("=" * 60)
        
        # The issue is that google_sheet_triggers.sheet_id is character varying
        # but google_sheets.id is UUID. We need to fix this.
        
        logger.info("""
🔍 PROBLEM ANALYSIS:
- google_sheet_triggers.sheet_id is character varying (string)
- google_sheets.id is UUID
- Foreign key constraint expects same data types

🔧 POSSIBLE SOLUTIONS:
1. Convert google_sheet_triggers.sheet_id to UUID type
2. Keep using google_sheets_v2 (if it has character varying id)
3. Update constraint to handle type conversion

📋 RECOMMENDED SOLUTION:
Convert google_sheet_triggers.sheet_id to UUID type to match google_sheets.id
        """)
        
        # Check current data in sheet_id column
        check_data_sql = """
        SELECT DISTINCT sheet_id, LEFT(sheet_id, 10) as sample
        FROM google_sheet_triggers 
        LIMIT 5;
        """
        
        existing_data = db.execute(text(check_data_sql)).fetchall()
        
        logger.info("📋 Current data in google_sheet_triggers.sheet_id:")
        for data in existing_data:
            logger.info(f"   {data[0]} (sample: {data[1]})")
        
        # Convert column type to UUID
        try:
            logger.info("🔄 Converting google_sheet_triggers.sheet_id to UUID type...")
            
            # First, drop the foreign key constraint
            drop_constraint_sql = """
            ALTER TABLE google_sheet_triggers 
            DROP CONSTRAINT IF EXISTS google_sheet_triggers_sheet_id_fkey;
            """
            
            db.execute(text(drop_constraint_sql))
            logger.info("🗑️  Dropped existing constraint")
            
            # Convert the column type
            convert_column_sql = """
            ALTER TABLE google_sheet_triggers 
            ALTER COLUMN sheet_id TYPE UUID USING sheet_id::UUID;
            """
            
            db.execute(text(convert_column_sql))
            logger.info("🔄 Converted sheet_id column to UUID type")
            
            # Recreate the foreign key constraint
            add_constraint_sql = """
            ALTER TABLE google_sheet_triggers 
            ADD CONSTRAINT google_sheet_triggers_sheet_id_fkey 
            FOREIGN KEY (sheet_id) 
            REFERENCES google_sheets(id) 
            ON DELETE CASCADE;
            """
            
            db.execute(text(add_constraint_sql))
            db.commit()
            logger.info("✅ Recreated foreign key constraint with UUID type")
            
            # Verify the fix
            verify_types_sql = """
            SELECT column_name, data_type
            FROM information_schema.columns 
            WHERE table_name = 'google_sheet_triggers' 
            AND column_name = 'sheet_id';
            """
            
            verify_col = db.execute(text(verify_types_sql)).fetchone()
            logger.info("📋 Updated column type:")
            logger.info(f"   Column: {verify_col[0]}")
            logger.info(f"   Data Type: {verify_col[1]}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error during conversion: {e}")
            db.rollback()
            return False
        
    except Exception as e:
        logger.error(f"❌ Error fixing data type: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    types = check_column_types()
    success = fix_data_type_mismatch()
    
    if success:
        logger.info("\n✅ DATA TYPE FIX COMPLETED!")
        logger.info("🚀 Foreign key constraint should now work!")
    else:
        logger.error("\n❌ Data type fix failed")
