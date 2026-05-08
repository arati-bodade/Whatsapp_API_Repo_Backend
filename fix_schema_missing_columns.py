import logging
import time
from sqlalchemy import text
from db.base import engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_schema():
    logger.info("🔧 Starting schema fix...")
    
    with engine.connect() as connection:
        # 1. Fix DEVICES table
        try:
            logger.info("Checking 'devices' table...")
            
            # Add qr_code column
            connection.execute(text("ALTER TABLE devices ADD COLUMN IF NOT EXISTS qr_code TEXT;"))
            logger.info("✅ Added 'qr_code' to devices")
            
            # Add deleted_at column
            connection.execute(text("ALTER TABLE devices ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL;"))
            logger.info("✅ Added 'deleted_at' to devices")
            
        except Exception as e:
            logger.error(f"❌ Error updating devices table: {e}")
            
        # 2. Fix GOOGLE_SHEETS table
        try:
            logger.info("Checking 'google_sheets' table...")
            
            # Add device_id column
            connection.execute(text("ALTER TABLE google_sheets ADD COLUMN IF NOT EXISTS device_id UUID DEFAULT NULL;"))
            logger.info("✅ Added 'device_id' to google_sheets")
            
        except Exception as e:
            logger.error(f"❌ Error updating google_sheets table: {e}")
            
        # Commit changes
        connection.commit()
        logger.info("🚀 Schema fix completed!")

if __name__ == "__main__":
    fix_schema()
