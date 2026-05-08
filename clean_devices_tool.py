import os
import requests
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def clean_system():
    db_url = os.getenv("DATABASE_URL")
    engine_url = os.getenv("WHATSAPP_ENGINE_URL", "http://localhost:3002")
    
    if not db_url:
        logger.error("DATABASE_URL not found in .env")
        return

    logger.info("🧹 STARTING SYSTEM-WIDE CLEANUP (NUCLEAR OPTION)")
    logger.info("=" * 60)

    # 1. Connect to Database
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # Step A: Engine Cleanup
        logger.info("Step 1: Cleaning up WhatsApp Engine sessions...")
        try:
            # Get all devices to delete their sessions explicitly
            result = db.execute(text("SELECT device_id FROM devices")).fetchall()
            device_ids = [str(r[0]) for r in result]
            
            logger.info(f"Found {len(device_ids)} devices to logout from engine.")
            
            for d_id in device_ids:
                try:
                    logger.info(f"   Deleting engine session: {d_id}")
                    # Using a 2s timeout for speed, most cleanups should be fast
                    requests.delete(f"{engine_url}/session/{d_id}", timeout=5)
                except Exception as e:
                    logger.warning(f"   Could not delete engine session {d_id}: {e}")
            
            # Additional safety: Try to clear all sessions if engine supports a mass clear
            # Even if it doesn't, we've tried for each known device.
        except Exception as e:
            logger.error(f"Error during engine cleanup phase: {e}")

        # Step B: Database Truncation
        logger.info("Step 2: Emptying database tables...")
        
        # Order matters due to foreign keys if they exist
        tables_to_clean = [
            "sheet_trigger_history",
            "google_sheet_triggers",
            "google_sheets",
            "whatsapp_messages",
            "whatsapp_inbox",
            "device_sessions",
            "devices"
        ]
        
        for table in tables_to_clean:
            try:
                # Check if table exists before trying to delete
                res = db.execute(text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')"))
                exists = res.scalar()
                
                if exists:
                    logger.info(f"   Dropping content from '{table}'...")
                    # We use DELETE instead of TRUNCATE to avoid potential lock issues on some hosted DBs, 
                    # and ensure cascade if needed (though we handling order here).
                    count_res = db.execute(text(f"DELETE FROM {table}"))
                    logger.info(f"   ✅ Deleted {count_res.rowcount} rows from {table}")
                else:
                    logger.info(f"   Table '{table}' does not exist, skipping.")
            except Exception as e:
                logger.error(f"   ❌ Error cleaning table {table}: {e}")
                db.rollback()

        # Commit all deletions
        db.commit()
        logger.info("=" * 60)
        logger.info("✅ NUCLEAR CLEANUP COMPLETE. System is now empty.")

    except Exception as e:
        logger.error(f"FATAL ERROR during cleanup: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    confirm = input("WARNING: This will delete ALL devices and messages. Type 'RESTORE' to confirm: ")
    if confirm == "RESTORE":
        clean_system()
    else:
        print("Cleanup cancelled.")
