#!/usr/bin/env python3
"""
Check and clean sheet_trigger_history table
"""

import logging
from sqlalchemy import text
from db.session import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_and_clean_trigger_history():
    """Check table structure and clean the trigger history table"""
    db = SessionLocal()
    try:
        logger.info("=== CHECKING SHEET_TRIGGER_HISTORY TABLE ===")
        
        # Check if table exists
        try:
            result = db.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'sheet_trigger_history'
                ORDER BY ordinal_position
            """))
            
            columns = result.fetchall()
            logger.info('Table structure:')
            for col in columns:
                logger.info(f'  {col[0]}: {col[1]} (nullable: {col[2]})')
                
        except Exception as e:
            logger.error(f'Table does not exist or error checking structure: {e}')
            return
        
        # Count records
        result = db.execute(text('SELECT COUNT(*) FROM sheet_trigger_history'))
        count = result.scalar()
        logger.info(f'Total records: {count}')
        
        # Show sample data if exists
        if count > 0:
            result = db.execute(text('SELECT trigger_id, status, triggered_at FROM sheet_trigger_history ORDER BY triggered_at DESC LIMIT 5'))
            records = result.fetchall()
            logger.info('Sample records:')
            for record in records:
                logger.info(f'  ID: {record[0]}, Status: {record[1]}, Time: {record[2]}')
        
        # Clean the table if it has records
        if count > 0:
            logger.info(f"Cleaning {count} records from sheet_trigger_history...")
            result = db.execute(text('DELETE FROM sheet_trigger_history'))
            deleted = result.rowcount
            db.commit()
            logger.info(f'  Deleted {deleted} records')
            
            # Verify cleanup
            result = db.execute(text('SELECT COUNT(*) FROM sheet_trigger_history'))
            final_count = result.scalar()
            logger.info(f'  Final record count: {final_count}')
        else:
            logger.info('No records to clean')
            
    except Exception as e:
        logger.error(f'Error: {e}')
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    check_and_clean_trigger_history()
