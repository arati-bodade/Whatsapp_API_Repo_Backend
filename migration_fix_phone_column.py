#!/usr/bin/env python3
"""
Migration script to add missing phone_column, status_column, trigger_value, message_template columns to google_sheet_triggers table
"""

import logging
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_database_url():
    """Get database URL from environment or .env file"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        import os
        return os.getenv("DATABASE_URL")
    except ImportError:
        logger.error("python-dotenv not installed. Please install it or set DATABASE_URL manually")
        return None

def check_column_exists(engine, table_name, column_name):
    """Check if a column exists in a table"""
    try:
        with engine.connect() as conn:
            # Query PostgreSQL information_schema
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

def add_missing_columns(engine):
    """Add missing columns to google_sheet_triggers table"""
    try:
        with engine.connect() as conn:
            # List of columns to add with their definitions
            columns_to_add = [
                ("phone_column", "VARCHAR(255) DEFAULT 'phone' NOT NULL"),
                ("status_column", "VARCHAR(255) DEFAULT 'Status' NOT NULL"),
                ("trigger_value", "VARCHAR(255) DEFAULT 'Send' NOT NULL"),
                ("message_template", "TEXT")
            ]
            
            for column_name, column_def in columns_to_add:
                if not check_column_exists(engine, "google_sheet_triggers", column_name):
                    logger.info(f"Adding {column_name} column to google_sheet_triggers...")
                    alter_sql = text(f"""
                        ALTER TABLE google_sheet_triggers 
                        ADD COLUMN {column_name} {column_def}
                    """)
                    conn.execute(alter_sql)
                    logger.info(f"✅ Successfully added {column_name} column")
                else:
                    logger.info(f"✅ Column {column_name} already exists")
            
            conn.commit()
            logger.info("✅ All missing columns added successfully")
            return True
            
    except SQLAlchemyError as e:
        logger.error(f"❌ Database error adding columns: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error adding columns: {e}")
        return False

def verify_columns_added(engine):
    """Verify all columns were added successfully"""
    required_columns = ["phone_column", "status_column", "trigger_value", "message_template"]
    all_exist = True
    
    for column_name in required_columns:
        exists = check_column_exists(engine, "google_sheet_triggers", column_name)
        if exists:
            logger.info(f"✅ Verification successful: {column_name} column exists")
        else:
            logger.error(f"❌ Verification failed: {column_name} column still missing")
            all_exist = False
    
    return all_exist

def main():
    """Main migration function"""
    logger.info("🚀 Starting migration: Add missing columns to google_sheet_triggers")
    
    # Get database URL
    database_url = get_database_url()
    if not database_url:
        logger.error("❌ DATABASE_URL not found. Please set it in .env file or environment.")
        sys.exit(1)
    
    logger.info(f"Connecting to database...")
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        # Add missing columns
        if not add_missing_columns(engine):
            logger.error("❌ Failed to add columns")
            sys.exit(1)
        
        # Verify the columns were added
        if not verify_columns_added(engine):
            logger.error("❌ Column verification failed")
            sys.exit(1)
        
        logger.info("🎉 Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
