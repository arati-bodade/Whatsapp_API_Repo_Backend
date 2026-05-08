#!/usr/bin/env python3
"""
Create missing sheet_trigger_history table
"""

import logging
from sqlalchemy import text
from db.session import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_trigger_history_table():
    """Create the missing sheet_trigger_history table"""
    logger.info("Creating sheet_trigger_history table...")
    
    db = SessionLocal()
    try:
        # SQL to create the table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS sheet_trigger_history (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            sheet_id UUID NOT NULL REFERENCES google_sheets(id) ON DELETE CASCADE,
            trigger_id VARCHAR(255) NOT NULL,
            row_number INTEGER,
            phone_number VARCHAR(50) NOT NULL,
            message_content TEXT NOT NULL,
            status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
            error_message TEXT,
            triggered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            row_data JSON,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_sheet_trigger_history_sheet_id 
            ON sheet_trigger_history(sheet_id);
            
        CREATE INDEX IF NOT EXISTS idx_sheet_trigger_history_triggered_at 
            ON sheet_trigger_history(triggered_at DESC);
        """
        
        db.execute(text(create_table_sql))
        db.commit()
        logger.info("Table created successfully!")
        
        # Verify table exists
        result = db.execute(text("SELECT COUNT(*) FROM sheet_trigger_history"))
        count = result.scalar()
        logger.info(f"Current record count: {count}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating table: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = create_trigger_history_table()
    
    if success:
        logger.info("Trigger history table fix complete!")
    else:
        logger.info("Table creation failed!")
