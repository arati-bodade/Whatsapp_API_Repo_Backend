import os
import logging
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def clean_devices_and_triggers():
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        logger.error("DATABASE_URL not found in .env")
        return

    logger.info("🧹 STARTING CLEANUP OF DEVICES AND TRIGGERS")
    logger.info("=" * 60)

    # Connect to Database
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        try:
            # Step 1: Check current data
            logger.info("Step 1: Checking current data...")
            
            # Check devices
            result = conn.execute(text("SELECT COUNT(*) FROM devices"))
            device_count = result.scalar()
            logger.info(f"   Devices table count: {device_count}")
            
            # Check triggers
            result = conn.execute(text("SELECT COUNT(*) FROM google_sheet_triggers"))
            trigger_count = result.scalar()
            logger.info(f"   Google Sheet Triggers table count: {trigger_count}")
            
            logger.info()
            
            # Step 2: Clean triggers first (due to potential foreign key constraints)
            logger.info("Step 2: Cleaning triggers table...")
            if trigger_count > 0:
                result = conn.execute(text("DELETE FROM google_sheet_triggers"))
                logger.info(f"   ✅ Deleted {result.rowcount} rows from google_sheet_triggers")
            else:
                logger.info("   No triggers to delete")
            
            # Step 3: Clean devices
            logger.info("Step 3: Cleaning devices table...")
            if device_count > 0:
                result = conn.execute(text("DELETE FROM devices"))
                logger.info(f"   ✅ Deleted {result.rowcount} rows from devices")
            else:
                logger.info("   No devices to delete")
            
            # Commit all deletions
            conn.commit()
            logger.info("=" * 60)
            logger.info("✅ CLEANUP COMPLETE. Devices and triggers tables are now empty.")
            
            # Step 4: Verify cleanup
            logger.info("Step 4: Verifying cleanup...")
            result = conn.execute(text("SELECT COUNT(*) FROM devices"))
            final_device_count = result.scalar()
            
            result = conn.execute(text("SELECT COUNT(*) FROM google_sheet_triggers"))
            final_trigger_count = result.scalar()
            
            logger.info(f"   Final devices count: {final_device_count}")
            logger.info(f"   Final triggers count: {final_trigger_count}")
            
            if final_device_count == 0 and final_trigger_count == 0:
                logger.info("   ✅ Verification successful - both tables are empty")
            else:
                logger.warning("   ⚠️ Verification failed - tables may not be completely empty")

        except Exception as e:
            logger.error(f"FATAL ERROR during cleanup: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    confirm = input("WARNING: This will delete ALL devices and triggers. Type 'CLEAN' to confirm: ")
    if confirm == "CLEAN":
        clean_devices_and_triggers()
    else:
        print("Cleanup cancelled.")
