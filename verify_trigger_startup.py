#!/usr/bin/env python3
"""
Verify Google Sheets triggers startup fixes
"""

import asyncio
import logging
from sqlalchemy import text
from db.session import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_trigger_startup():
    """Test the trigger startup function with timeout"""
    try:
        logger.info("=== TESTING GOOGLE SHEETS TRIGGERS STARTUP ===")
        
        # Import the function
        from api.google_sheets import start_all_enabled_triggers_on_boot
        
        # Test with timeout
        logger.info("Testing trigger startup with 30-second timeout...")
        count = await asyncio.wait_for(start_all_enabled_triggers_on_boot(), timeout=30.0)
        logger.info(f"SUCCESS: Started {count} triggers")
        
    except asyncio.TimeoutError:
        logger.error("TIMEOUT: Trigger startup took too long - this indicates the fix is needed")
        return False
    except Exception as e:
        logger.error(f"ERROR: {e}")
        return False
    
    return True

def check_database_connection():
    """Test database connection speed"""
    db = SessionLocal()
    try:
        logger.info("Testing database connection...")
        result = db.execute(text('SELECT 1'))
        result.scalar()
        logger.info("Database connection OK")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    # Test database connection first
    if not check_database_connection():
        logger.error("Database connection issues detected")
        exit(1)
    
    # Test trigger startup
    success = asyncio.run(test_trigger_startup())
    
    if success:
        logger.info("=== ALL TESTS PASSED ===")
        logger.info("Google Sheets triggers startup is working correctly")
    else:
        logger.error("=== TESTS FAILED ===")
        logger.error("Issues detected with trigger startup")
