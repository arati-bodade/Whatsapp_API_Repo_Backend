#!/usr/bin/env python3
"""
Database Connection Monitor - Runs continuously and reconnects if needed
"""

import time
import logging
from datetime import datetime
from sqlalchemy import create_engine, text, exc

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [DB_MONITOR] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database URL
DATABASE_URL = "postgresql://whatsapp_platform_mhnw_user:nComdm17QkuwCzuxi2sMjZrIbXXLV8FG@dpg-d7cbd05ckfvc7387lfog-a.oregon-postgres.render.com/whatsapp_platform_mhnw"

def create_engine():
    """Create database engine with robust settings"""
    return create_engine(
        DATABASE_URL,
        pool_size=2,
        max_overflow=5,
        pool_timeout=60,
        pool_recycle=120,
        pool_pre_ping=True,
        connect_args={
            "connect_timeout": 60,
            "sslmode": "require",
            "application_name": "whatsapp_platform_monitor"
        }
    )

def check_connection():
    """Check database connection"""
    try:
        engine = create_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            engine.dispose()
            return True
    except Exception as e:
        logger.error(f"Connection check failed: {e}")
        return False

def monitor_loop():
    """Main monitoring loop"""
    logger.info("Starting database connection monitor...")
    
    consecutive_failures = 0
    max_failures = 3
    
    while True:
        try:
            if check_connection():
                logger.info("Database connection is healthy")
                consecutive_failures = 0
            else:
                consecutive_failures += 1
                logger.error(f"Connection failed! Attempt {consecutive_failures}/{max_failures}")
                
                if consecutive_failures >= max_failures:
                    logger.error("Max failures reached. Attempting to reconnect...")
                    # Force engine recreation
                    try:
                        engine = create_engine()
                        with engine.connect() as conn:
                            result = conn.execute(text("SELECT 1"))
                        logger.info("Reconnection successful!")
                        consecutive_failures = 0
                    except Exception as e:
                        logger.error(f"Reconnection failed: {e}")
            
            # Wait 30 seconds before next check
            time.sleep(30)
            
        except KeyboardInterrupt:
            logger.info("Monitor stopped by user")
            break
        except Exception as e:
            logger.error(f"Monitor error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    monitor_loop()
