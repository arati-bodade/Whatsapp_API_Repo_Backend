#!/usr/bin/env python3
"""
Fix database connection pool overflow issue
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
import logging

# Database URL
DATABASE_URL = "postgresql://whatsapp_platform_fn0k_user:AbHezwfAs553dVCy33wfHzsGMVJbf8M0@dpg-d6oh8tfafjfc7386oii0-a.oregon-postgres.render.com/whatsapp_platform_fn0k"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fix_database_pool():
    """Fix database connection pool settings"""
    
    logger.info("🔧 FIXING DATABASE CONNECTION POOL")
    logger.info("=" * 40)
    
    try:
        # Create engine with larger pool settings
        engine = create_engine(
            DATABASE_URL,
            pool_size=20,           # Increase from 5 to 20
            max_overflow=30,        # Increase from 10 to 30
            pool_timeout=60,        # Increase from 30 to 60
            pool_recycle=3600,      # Recycle connections every hour
            pool_pre_ping=True      # Validate connections before use
        )
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            test_value = result.fetchone()[0]
            logger.info(f"✅ Database connection test: {test_value}")
        
        logger.info("✅ New pool settings:")
        logger.info(f"   Pool size: 20 (was 5)")
        logger.info(f"   Max overflow: 30 (was 10)")
        logger.info(f"   Pool timeout: 60s (was 30s)")
        logger.info(f"   Pool recycle: 3600s")
        logger.info(f"   Pre-ping: True")
        
        return engine
        
    except Exception as e:
        logger.error(f"❌ Error fixing pool: {e}")
        return None

def update_config_file():
    """Update config.py with new database settings"""
    
    logger.info("📝 UPDATING CONFIG.PY")
    
    config_path = os.path.join(os.path.dirname(__file__), 'core', 'config.py')
    
    try:
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Add pool settings if not present
        if 'pool_size=' not in content:
            new_engine_code = '''
# Database engine with connection pool settings
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_timeout=60,
    pool_recycle=3600,
    pool_pre_ping=True
)
'''
            
            # Find the DATABASE_URL line and add engine after it
            lines = content.split('\n')
            new_lines = []
            
            for line in lines:
                new_lines.append(line)
                if 'DATABASE_URL = ' in line:
                    new_lines.append(new_engine_code)
            
            with open(config_path, 'w') as f:
                f.write('\n'.join(new_lines))
            
            logger.info("✅ Updated config.py with pool settings")
            
        else:
            logger.info("✅ Pool settings already exist in config.py")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error updating config: {e}")
        return False

def main():
    """Main function"""
    logger.info("🚀 DATABASE POOL FIX")
    
    # Test new pool settings
    engine = fix_database_pool()
    
    if engine:
        # Update config file
        update_config_file()
        
        logger.info("\n🎉 POOL FIX COMPLETED!")
        logger.info("✅ Restart backend to apply new settings")
        logger.info("✅ This should fix the connection timeout errors")
        
    else:
        logger.error("❌ Pool fix failed")

if __name__ == "__main__":
    main()
