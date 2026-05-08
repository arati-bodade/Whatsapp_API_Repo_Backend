#!/usr/bin/env python3
"""
Debug Google Sheets foreign key constraint violation
"""

import logging
from sqlalchemy import text
from db.session import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_google_sheets_tables():
    """Check Google Sheets tables and their structure"""
    db = SessionLocal()
    try:
        logger.info("🔍 CHECKING GOOGLE SHEETS TABLES")
        logger.info("=" * 60)
        
        # Check what Google Sheets tables exist
        tables_sql = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_name LIKE '%google_sheet%' 
        ORDER BY table_name;
        """
        
        tables = db.execute(text(tables_sql)).fetchall()
        
        logger.info("📋 Google Sheets related tables:")
        for table in tables:
            logger.info(f"   📁 {table[0]}")
        
        # Check the specific sheet ID that's causing the error
        sheet_id = "b9a9f439-6e73-4ab4-b9cf-12b64f2c4893"
        
        logger.info(f"\n🔍 CHECKING SHEET ID: {sheet_id}")
        
        # Check in google_sheets table
        check_google_sheets_sql = """
        SELECT id, sheet_name, user_id, created_at 
        FROM google_sheets 
        WHERE id = :sheet_id;
        """
        
        result = db.execute(text(check_google_sheets_sql), {"sheet_id": sheet_id}).fetchone()
        
        if result:
            logger.info("✅ Sheet found in google_sheets table:")
            logger.info(f"   ID: {result[0]}")
            logger.info(f"   Name: {result[1]}")
            logger.info(f"   User ID: {result[2]}")
            logger.info(f"   Created: {result[3]}")
        else:
            logger.warning("❌ Sheet NOT found in google_sheets table")
        
        # Check in google_sheets_v2 table (mentioned in error)
        check_google_sheets_v2_sql = """
        SELECT id, sheet_name, user_id, created_at 
        FROM google_sheets_v2 
        WHERE id = :sheet_id;
        """
        
        try:
            result_v2 = db.execute(text(check_google_sheets_v2_sql), {"sheet_id": sheet_id}).fetchone()
            
            if result_v2:
                logger.info("✅ Sheet found in google_sheets_v2 table:")
                logger.info(f"   ID: {result_v2[0]}")
                logger.info(f"   Name: {result_v2[1]}")
                logger.info(f"   User ID: {result_v2[2]}")
                logger.info(f"   Created: {result_v2[3]}")
            else:
                logger.warning("❌ Sheet NOT found in google_sheets_v2 table")
        except Exception as e:
            logger.info(f"📋 google_sheets_v2 table doesn't exist: {e}")
        
        # Check all sheets in both tables
        logger.info(f"\n📊 ALL SHEETS IN DATABASE:")
        
        # Count sheets in google_sheets
        count_google_sheets = db.execute(text("SELECT COUNT(*) FROM google_sheets")).scalar()
        logger.info(f"   📁 google_sheets: {count_google_sheets} sheets")
        
        # Try to count sheets in google_sheets_v2
        try:
            count_google_sheets_v2 = db.execute(text("SELECT COUNT(*) FROM google_sheets_v2")).scalar()
            logger.info(f"   📁 google_sheets_v2: {count_google_sheets_v2} sheets")
        except:
            logger.info(f"   📁 google_sheets_v2: table doesn't exist")
        
        # Show sample sheets from google_sheets
        sample_sheets = db.execute(text("""
        SELECT id, sheet_name, user_id, created_at 
        FROM google_sheets 
        ORDER BY created_at DESC 
        LIMIT 5;
        """)).fetchall()
        
        logger.info(f"\n📋 Sample sheets from google_sheets:")
        for sheet in sample_sheets:
            logger.info(f"   📁 {sheet[0]} - {sheet[1]} (User: {sheet[2]})")
        
        return {
            "tables": [t[0] for t in tables],
            "sheet_exists_in_google_sheets": bool(result),
            "sheet_exists_in_google_sheets_v2": bool(result_v2) if 'result_v2' in locals() else False
        }
        
    except Exception as e:
        logger.error(f"❌ Error checking tables: {e}")
        return None
    finally:
        db.close()

def check_foreign_key_constraints():
    """Check foreign key constraints on google_sheet_triggers"""
    db = SessionLocal()
    try:
        logger.info("\n🔗 CHECKING FOREIGN KEY CONSTRAINTS")
        logger.info("=" * 60)
        
        # Check constraints on google_sheet_triggers
        constraints_sql = """
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
        AND tc.table_name = 'google_sheet_triggers';
        """
        
        constraints = db.execute(text(constraints_sql)).fetchall()
        
        logger.info("📋 Foreign key constraints on google_sheet_triggers:")
        for constraint in constraints:
            logger.info(f"   🔗 {constraint[0]}")
            logger.info(f"      {constraint[1]}.{constraint[2]} -> {constraint[3]}.{constraint[4]}")
        
        return constraints
        
    except Exception as e:
        logger.error(f"❌ Error checking constraints: {e}")
        return None
    finally:
        db.close()

def fix_sheet_reference():
    """Fix the sheet reference issue"""
    logger.info("\n🔧 FIXING SHEET REFERENCE ISSUE")
    logger.info("=" * 60)
    
    logger.info("""
🔍 PROBLEM ANALYSIS:
1. Sheet ID exists in google_sheets table
2. Foreign key constraint points to google_sheets_v2 table
3. This is a table reference mismatch

🔧 POSSIBLE SOLUTIONS:
1. Update foreign key to point to google_sheets table
2. Move sheet to google_sheets_v2 table
3. Check which table is correct for the application

📋 RECOMMENDED FIX:
Update the foreign key constraint to reference google_sheets table
instead of google_sheets_v2 table, since that's where the sheet exists.
    """)

if __name__ == "__main__":
    result = check_google_sheets_tables()
    constraints = check_foreign_key_constraints()
    fix_sheet_reference()
    
    logger.info("\n✅ DIAGNOSIS COMPLETED")
    if result:
        logger.info(f"📊 Tables found: {result['tables']}")
        logger.info(f"📁 Sheet in google_sheets: {result['sheet_exists_in_google_sheets']}")
        logger.info(f"📁 Sheet in google_sheets_v2: {result['sheet_exists_in_google_sheets_v2']}")
