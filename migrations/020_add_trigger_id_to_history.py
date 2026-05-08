#!/usr/bin/env python3
"""
Migration to add trigger_id column to sheet_trigger_history table
This column is needed to track which trigger caused the history entry
"""

import logging
import sys
import os
from sqlalchemy import text

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.session import get_db

logger = logging.getLogger(__name__)

def add_trigger_id_column():
    """Add trigger_id column to sheet_trigger_history table"""
    try:
        db = next(get_db())
        
        # Check if column exists
        check_column_sql = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'sheet_trigger_history' 
        AND column_name = 'trigger_id';
        """
        
        result = db.execute(text(check_column_sql)).fetchone()
        
        if not result:
            logger.info("🔧 Adding trigger_id column to sheet_trigger_history...")
            
            # Add the column
            add_column_sql = """
            ALTER TABLE sheet_trigger_history 
            ADD COLUMN trigger_id VARCHAR(255) NULL;
            """
            
            db.execute(text(add_column_sql))
            db.commit()
            
            logger.info("✅ Successfully added trigger_id column to sheet_trigger_history")
            
            # Create index for better performance
            create_index_sql = """
            CREATE INDEX IF NOT EXISTS idx_sheet_trigger_history_trigger_id 
            ON sheet_trigger_history(trigger_id);
            """
            
            try:
                db.execute(text(create_index_sql))
                db.commit()
                logger.info("✅ Successfully created index on trigger_id")
            except Exception as e:
                logger.warning(f"Index creation failed (may already exist): {e}")
                
        else:
            logger.info("ℹ️ trigger_id column already exists in sheet_trigger_history")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to add trigger_id column: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = add_trigger_id_column()
    if success:
        print("🎉 Migration completed successfully!")
    else:
        print("❌ Migration failed!")
        exit(1)
