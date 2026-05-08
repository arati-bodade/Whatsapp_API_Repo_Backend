#!/usr/bin/env python3
"""
Database Connection Checker and Auto-Reconnector
Tests database connectivity and reconnects if needed
"""

import sys
import os
import time
import logging
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text, exc
from sqlalchemy.pool import QueuePool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database URLs from user
EXTERNAL_DB_URL = "postgresql://whatsapp_platform_mhnw_user:nComdm17QkuwCzuxi2sMjZrIbXXLV8FG@dpg-d7cbd05ckfvc7387lfog-a.oregon-postgres.render.com/whatsapp_platform_mhnw"
INTERNAL_DB_URL = "postgresql://whatsapp_platform_mhnw_user:nComdm17QkuwCzuxi2sMjZrIbXXLV8FG@dpg-d7cbd05ckfvc7387lfog-a/whatsapp_platform_mhnw"

def test_connection(url, name="Database"):
    """Test database connection with given URL"""
    logger.info(f"Testing {name} connection...")
    
    try:
        # Create engine with robust settings
        engine = create_engine(
            url,
            poolclass=QueuePool,
            pool_size=1,
            max_overflow=0,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True,
            connect_args={
                "connect_timeout": 30,
                "sslmode": "require",
                "application_name": "connection_checker"
            }
        )
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test, version() as version, now() as timestamp"))
            row = result.first()
            
            logger.info(f"  {name}: CONNECTION SUCCESSFUL")
            logger.info(f"    Test Query Result: {row[0]}")
            logger.info(f"    PostgreSQL Version: {row[1][:50]}...")
            logger.info(f"    Server Timestamp: {row[2]}")
            
            # Get database info
            try:
                result = conn.execute(text("SELECT current_database() as db_name, current_user() as user"))
                info = result.first()
                logger.info(f"    Database: {info[0]}")
                logger.info(f"    User: {info[1]}")
            except Exception as e:
                logger.warning(f"    Could not get database info: {e}")
            
            engine.dispose()
            return True
            
    except exc.OperationalError as e:
        logger.error(f"  {name}: CONNECTION FAILED - Operational Error")
        logger.error(f"    Error: {e}")
        return False
    except exc.InterfaceError as e:
        logger.error(f"  {name}: CONNECTION FAILED - Interface Error")
        logger.error(f"    Error: {e}")
        return False
    except Exception as e:
        logger.error(f"  {name}: CONNECTION FAILED - Unknown Error")
        logger.error(f"    Error: {e}")
        return False

def check_current_config():
    """Check current configuration in core/config.py"""
    try:
        from core.config import settings
        logger.info("Current configuration from core/config.py:")
        logger.info(f"  DATABASE_URL: {settings.DATABASE_URL}")
        return settings.DATABASE_URL
    except Exception as e:
        logger.error(f"Could not read current config: {e}")
        return None

def create_connection_monitor():
    """Create a connection monitor script"""
    monitor_script = '''#!/usr/bin/env python3
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
'''
    
    with open('database_connection_monitor.py', 'w') as f:
        f.write(monitor_script)
    
    logger.info("Created database_connection_monitor.py for continuous monitoring")

def main():
    """Main function"""
    logger.info("DATABASE CONNECTION CHECKER")
    logger.info("=" * 50)
    logger.info(f"Timestamp: {datetime.now()}")
    logger.info("")
    
    # Check current configuration
    current_url = check_current_config()
    logger.info("")
    
    # Test external URL
    external_success = test_connection(EXTERNAL_DB_URL, "External Database")
    logger.info("")
    
    # Test internal URL  
    internal_success = test_connection(INTERNAL_DB_URL, "Internal Database")
    logger.info("")
    
    # Compare with current config
    if current_url:
        if current_url == EXTERNAL_DB_URL:
            logger.info("Current config matches EXTERNAL URL")
        elif current_url == INTERNAL_DB_URL:
            logger.info("Current config matches INTERNAL URL")
        else:
            logger.warning("Current config does not match either provided URL")
            logger.warning(f"Current: {current_url}")
    
    # Summary
    logger.info("")
    logger.info("SUMMARY:")
    logger.info(f"  External URL: {'SUCCESS' if external_success else 'FAILED'}")
    logger.info(f"  Internal URL: {'SUCCESS' if internal_success else 'FAILED'}")
    
    # Recommendation
    if external_success and not internal_success:
        logger.info("")
        logger.info("RECOMMENDATION: Use External URL")
        logger.info("The external URL is working, internal is not.")
    elif internal_success and not external_success:
        logger.info("")
        logger.info("RECOMMENDATION: Use Internal URL")
        logger.info("The internal URL is working, external is not.")
    elif external_success and internal_success:
        logger.info("")
        logger.info("RECOMMENDATION: Both URLs work - choose based on your network setup")
        logger.info("External URL: For internet access")
        logger.info("Internal URL: For same-network access")
    else:
        logger.error("")
        logger.error("CRITICAL: Neither URL is working!")
        logger.error("Check your credentials and network connectivity")
    
    # Create monitor script
    logger.info("")
    create_connection_monitor()
    
    return external_success or internal_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
