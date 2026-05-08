#!/usr/bin/env python3
"""
Script to initialize all tables in the new PostgreSQL database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from db.base import Base, engine
from models import *  # Import all models to register them with Base.metadata
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_database_connection():
    """Test database connection"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("✅ Database connection successful")
            return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

def list_all_tables():
    """List all tables that will be created"""
    logger.info("📋 Tables that will be created:")
    for table_name in Base.metadata.tables.keys():
        logger.info(f"  - {table_name}")

def create_all_tables():
    """Create all tables in the database"""
    try:
        logger.info("🚀 Creating all tables...")
        Base.metadata.create_all(bind=engine, checkfirst=True)
        logger.info("✅ All tables created successfully!")
        
        # Verify tables were created
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            logger.info(f"📊 Total tables in database: {len(tables)}")
            for table in tables:
                logger.info(f"  ✓ {table}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        return False

def create_indexes():
    """Create additional indexes for performance"""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_devices_busi_user_id ON devices(busi_user_id);",
        "CREATE INDEX IF NOT EXISTS idx_messages_busi_user_id ON messages(busi_user_id);",
        "CREATE INDEX IF NOT EXISTS idx_messages_device_id ON messages(device_id);",
        "CREATE INDEX IF NOT EXISTS idx_campaigns_busi_user_id ON campaigns(busi_user_id);",
        "CREATE INDEX IF NOT EXISTS idx_google_sheets_user_id ON google_sheets(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_sheet_trigger_history_sheet_id ON sheet_trigger_history(sheet_id);",
        "CREATE INDEX IF NOT EXISTS idx_whatsapp_inbox_busi_user_id ON whatsapp_inbox(busi_user_id);",
        "CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_busi_user_id ON whatsapp_messages(busi_user_id);",
    ]
    
    try:
        logger.info("🔧 Creating performance indexes...")
        with engine.connect() as conn:
            for index_sql in indexes:
                conn.execute(text(index_sql))
            conn.commit()
        logger.info("✅ Performance indexes created successfully!")
        return True
    except Exception as e:
        logger.error(f"❌ Error creating indexes: {e}")
        return False

def main():
    """Main function to set up the database"""
    logger.info("🎯 Starting database setup for new PostgreSQL instance...")
    
    # Check database connection
    if not check_database_connection():
        logger.error("❌ Cannot proceed without database connection")
        sys.exit(1)
    
    # List tables to be created
    list_all_tables()
    
    # Create all tables
    if not create_all_tables():
        logger.error("❌ Failed to create tables")
        sys.exit(1)
    
    # Create performance indexes
    if not create_indexes():
        logger.warning("⚠️  Some indexes may not have been created, but tables are ready")
    
    logger.info("🎉 Database setup completed successfully!")
    logger.info("📝 Your new PostgreSQL database is ready with all required tables!")

if __name__ == "__main__":
    main()
