#!/usr/bin/env python3
"""
Migration to remove device_id columns from Google Sheet tables
These columns are no longer needed since we use Official WhatsApp Config
"""

import logging
import sys
import os
from sqlalchemy import text

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.session import get_db

logger = logging.getLogger(__name__)

def remove_device_id_columns():
    """Remove device_id columns from Google Sheet tables"""
    try:
        db = next(get_db())
        
        # Check and remove device_id from sheet_trigger_history
        check_history_sql = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'sheet_trigger_history' 
        AND column_name = 'device_id';
        """
        
        result = db.execute(text(check_history_sql)).fetchone()
        
        if result:
            logger.info("🔧 Found device_id in sheet_trigger_history, removing...")
            drop_history_sql = """
            ALTER TABLE sheet_trigger_history 
            DROP COLUMN IF EXISTS device_id;
            """
            db.execute(text(drop_history_sql))
            db.commit()
            logger.info("✅ Successfully removed device_id from sheet_trigger_history")
        else:
            logger.info("ℹ️ device_id column does not exist in sheet_trigger_history")
            
        # Check and remove device_id from google_sheet_triggers
        check_triggers_sql = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'google_sheet_triggers' 
        AND column_name = 'device_id';
        """
        
        result = db.execute(text(check_triggers_sql)).fetchone()
        
        if result:
            logger.info("🔧 Found device_id in google_sheet_triggers, removing...")
            drop_triggers_sql = """
            ALTER TABLE google_sheet_triggers 
            DROP COLUMN IF EXISTS device_id;
            """
            db.execute(text(drop_triggers_sql))
            db.commit()
            logger.info("✅ Successfully removed device_id from google_sheet_triggers")
        else:
            logger.info("ℹ️ device_id column does not exist in google_sheet_triggers")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to remove device_id columns: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = remove_device_id_columns()
    if success:
        print("🎉 Migration completed successfully!")
    else:
        print("❌ Migration failed!")
        exit(1)
