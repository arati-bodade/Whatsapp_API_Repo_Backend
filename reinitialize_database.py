import logging
import sys
import os

# Add the current directory to sys.path to allow imports
sys.path.append(os.getcwd())

from db.base import Base, engine
from db.init_db import init_db
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DB_REINIT")

def reinitialize_database():
    """Drops all tables and recreates them to fix schema inconsistencies."""
    logger.info("⚠️ CAUTION: Reinitializing database. This will wipe all data!")
    
    try:
        # 1. Drop all tables
        logger.info("🗑️ Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        
        # 2. Recreate all tables
        logger.info("🏗️ Recreating tables with standardized UUID schema...")
        init_db()
        
        logger.info("✅ Database successfully reinitialized!")
        
    except Exception as e:
        logger.error(f"❌ Failed to reinitialize database: {e}")
        # Try a more aggressive drop if metadata fails
        try:
            logger.info("🔄 Attempting aggressive cleanup...")
            with engine.connect() as conn:
                # Drop all tables in public schema
                conn.execute(text("""
                    DROP SCHEMA public CASCADE;
                    CREATE SCHEMA public;
                    GRANT ALL ON SCHEMA public TO public;
                    GRANT ALL ON SCHEMA public TO whatsapp_platform_mhnw_user;
                """))
                conn.commit()
            logger.info("🗑️ Schema purged. Recreating...")
            init_db()
            logger.info("✅ Aggressive reinitialization successful!")
        except Exception as e2:
            logger.error(f"❌ Aggressive cleanup failed: {e2}")

if __name__ == "__main__":
    reinitialize_database()
