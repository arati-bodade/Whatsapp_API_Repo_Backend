#!/usr/bin/env python3
"""
Migration 021: Add send_time_column and message_column to google_sheet_triggers
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
import logging

# Database URL
DATABASE_URL = "postgresql://whatsapp_platform_fn0k_user:AbHezwfAs553dVCy33wfHzsGMVJbf8M0@dpg-d6oh8tfafjfc7386oii0-a.oregon-postgres.render.com/whatsapp_platform_fn0k"

# Create engine
engine = create_engine(DATABASE_URL)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def add_send_time_and_message_columns():
    """Add send_time_column and message_column to google_sheet_triggers table"""
    
    logger.info("🔧 ADDING SEND_TIME AND MESSAGE COLUMNS")
    logger.info("=" * 50)
    
    try:
        with engine.connect() as conn:
            
            # Check if columns already exist
            logger.info("📋 Checking existing columns...")
            
            columns_result = conn.execute(text("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'google_sheet_triggers'
                ORDER BY ordinal_position
            """))
            existing_columns = [row[0] for row in columns_result.fetchall()]
            
            logger.info(f"   Existing columns: {existing_columns}")
            
            # Add send_time_column if it doesn't exist
            if 'send_time_column' not in existing_columns:
                logger.info("📋 Adding send_time_column...")
                conn.execute(text("""
                    ALTER TABLE google_sheet_triggers
                    ADD COLUMN send_time_column VARCHAR(255)
                """))
                logger.info("   ✅ send_time_column added")
            else:
                logger.info("   ✅ send_time_column already exists")
            
            # Add message_column if it doesn't exist
            if 'message_column' not in existing_columns:
                logger.info("📋 Adding message_column...")
                conn.execute(text("""
                    ALTER TABLE google_sheet_triggers
                    ADD COLUMN message_column VARCHAR(255)
                """))
                logger.info("   ✅ message_column added")
            else:
                logger.info("   ✅ message_column already exists")
            
            # Commit the changes
            conn.commit()
            logger.info("   ✅ Changes committed to database")
            
            # Verify the changes
            logger.info("📋 Verifying changes...")
            
            verify_result = conn.execute(text("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'google_sheet_triggers'
                AND column_name IN ('send_time_column', 'message_column')
                ORDER BY column_name
            """))
            verify_columns = verify_result.fetchall()
            
            logger.info("   📊 New columns added:")
            for col in verify_columns:
                logger.info(f"      {col[0]}: {col[1]}")
            
            logger.info("")
            logger.info("🎉 MIGRATION COMPLETED!")
            logger.info("✅ send_time_column added for time-based triggers")
            logger.info("✅ message_column added for sheet message content")
            logger.info("✅ Triggers can now use Send_time and Message columns")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

def main():
    """Main migration function"""
    success = add_send_time_and_message_columns()
    
    if success:
        logger.info("")
        logger.info("📝 NEXT STEPS:")
        logger.info("1. Restart the backend to use new model fields")
        logger.info("2. Test frontend with new Send_time and Message column options")
        logger.info("3. Create time-based triggers using Send_time column")
        logger.info("4. Test message content from Message column")
    else:
        logger.error("❌ Migration failed - please check the error above")

if __name__ == "__main__":
    main()
