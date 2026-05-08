#!/usr/bin/env python3
"""
Migration script to add missing last_processed_row column to google_sheet_triggers table
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

def add_last_processed_row_column(engine):
    """Add last_processed_row column to google_sheet_triggers table"""
    try:
        with engine.connect() as conn:
            # Add the column with DEFAULT 0 and NOT NULL constraint
            alter_sql = text("""
                ALTER TABLE google_sheet_triggers 
                ADD COLUMN IF NOT EXISTS last_processed_row INTEGER DEFAULT 0 NOT NULL
            """)
            
            logger.info("Adding last_processed_row column to google_sheet_triggers...")
            conn.execute(alter_sql)
            conn.commit()
            
            logger.info("✅ Successfully added last_processed_row column")
            return True
            
    except SQLAlchemyError as e:
        logger.error(f"❌ Database error adding column: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error adding column: {e}")
        return False

def verify_column_added(engine):
    """Verify the column was added successfully"""
    try:
        exists = check_column_exists(engine, "google_sheet_triggers", "last_processed_row")
        if exists:
            logger.info("✅ Verification successful: last_processed_row column exists")
            return True
        else:
            logger.error("❌ Verification failed: last_processed_row column still missing")
            return False
    except Exception as e:
        logger.error(f"❌ Error during verification: {e}")
        return False

def main():
    """Main migration function"""
    logger.info("🚀 Starting migration: Add last_processed_row column to google_sheet_triggers")
    
    # Get database URL
    database_url = get_database_url()
    if not database_url:
        logger.error("❌ DATABASE_URL not found. Please set it in .env file or environment.")
        sys.exit(1)
    
    logger.info(f"Connecting to database...")
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        # Check if column already exists
        if check_column_exists(engine, "google_sheet_triggers", "last_processed_row"):
            logger.info("✅ Column last_processed_row already exists. No migration needed.")
            sys.exit(0)
        
        # Add the column
        if not add_last_processed_row_column(engine):
            logger.error("❌ Failed to add column")
            sys.exit(1)
        
        # Verify the column was added
        if not verify_column_added(engine):
            logger.error("❌ Column verification failed")
            sys.exit(1)
        
        logger.info("🎉 Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
