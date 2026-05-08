#!/usr/bin/env python3
"""
Migration to remove official_message_id from sheet_trigger_history table
This column is not needed for trigger history functionality
"""

import logging
import sys
import os
from sqlalchemy import text

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.session import get_db

logger = logging.getLogger(__name__)

def remove_official_message_id_column():
    """Remove official_message_id column from sheet_trigger_history table"""
    try:
        db = next(get_db())
        
        # Check if column exists
        check_column_sql = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'sheet_trigger_history' 
        AND column_name = 'official_message_id';
        """
        
        result = db.execute(text(check_column_sql)).fetchone()
        
        if result:
            logger.info("🔧 Found official_message_id column, removing...")
            
            # Drop the column
            drop_column_sql = """
            ALTER TABLE sheet_trigger_history 
            DROP COLUMN IF EXISTS official_message_id;
            """
            
            db.execute(text(drop_column_sql))
            db.commit()
            
            logger.info("✅ Successfully removed official_message_id column from sheet_trigger_history")
            
            # Drop index if it exists
            drop_index_sql = """
            DROP INDEX IF EXISTS idx_sheet_trigger_history_official_msg_id;
            """
            
            try:
                db.execute(text(drop_index_sql))
                db.commit()
                logger.info("✅ Successfully removed index on official_message_id")
            except Exception as e:
                logger.warning(f"Index did not exist or could not be dropped: {e}")
                
        else:
            logger.info("ℹ️ official_message_id column does not exist in sheet_trigger_history")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to remove official_message_id column: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = remove_official_message_id_column()
    if success:
        print("🎉 Migration completed successfully!")
    else:
        print("❌ Migration failed!")
        exit(1)
