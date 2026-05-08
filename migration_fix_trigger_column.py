#!/usr/bin/env python3
"""
Add missing trigger_column to google_sheet_triggers table for backward compatibility
"""

import logging
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_database_url():
    try:
        from dotenv import load_dotenv
        load_dotenv()
        import os
        return os.getenv("DATABASE_URL")
    except ImportError:
        logger.error("python-dotenv not installed")
        return None

def check_column_exists(engine, table_name, column_name):
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = :table_name 
                AND column_name = :column_name
            """)
            result = conn.execute(query, {
                "table_name": table_name,
                "column_name": column_name
            })
            return result.fetchone() is not None
    except Exception as e:
        logger.error(f"Error checking column existence: {e}")
        return False

def add_trigger_column(engine):
    try:
        with engine.connect() as conn:
            if check_column_exists(engine, "google_sheet_triggers", "trigger_column"):
                logger.info("✅ trigger_column already exists")
                return True
            
            logger.info("Adding trigger_column to google_sheet_triggers...")
            alter_sql = text("""
                ALTER TABLE google_sheet_triggers 
                ADD COLUMN trigger_column VARCHAR(255) NULL
            """)
            
            conn.execute(alter_sql)
            conn.commit()
            
            logger.info("✅ Successfully added trigger_column")
            return True
            
    except SQLAlchemyError as e:
        logger.error(f"❌ Database error adding column: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error adding column: {e}")
        return False

def main():
    logger.info("🚀 Adding missing trigger_column to google_sheet_triggers")
    
    database_url = get_database_url()
    if not database_url:
        logger.error("❌ DATABASE_URL not found")
        sys.exit(1)
    
    try:
        engine = create_engine(database_url)
        
        if not add_trigger_column(engine):
            logger.error("❌ Failed to add trigger_column")
            sys.exit(1)
        
        logger.info("🎉 Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
