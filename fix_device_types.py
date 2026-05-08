#!/usr/bin/env python3
"""
🔧 DATABASE CLEANUP SCRIPT - Device Type Fixes

Fixes incorrect device_type values and adds proper constraints.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models.device import Device, DeviceType
from core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_session():
    """Get database session"""
    DATABASE_URL = settings.DATABASE_URL
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def check_device_type_distribution():
    """Check current device_type distribution"""
    db = get_db_session()
    try:
        result = db.execute(text("""
            SELECT device_type, COUNT(*) as count 
            FROM devices 
            WHERE is_active = true 
            GROUP BY device_type
            ORDER BY count DESC
        """))
        
        logger.info("📊 Current device_type distribution:")
        for row in result:
            logger.info(f"  {row.device_type}: {row.count} devices")
            
        # Check for any invalid device types
        result = db.execute(text("""
            SELECT DISTINCT device_type, COUNT(*) as count 
            FROM devices 
            WHERE is_active = true 
            AND device_type NOT IN ('web', 'official', 'mobile', 'desktop')
            GROUP BY device_type
        """))
        
        invalid_types = result.fetchall()
        if invalid_types:
            logger.warning("⚠️ Found invalid device types:")
            for row in invalid_types:
                logger.warning(f"  {row.device_type}: {row.count} devices")
        else:
            logger.info("✅ No invalid device types found")
            
    finally:
        db.close()

def fix_device_types():
    """Fix incorrect device_type values"""
    db = get_db_session()
    try:
        # Fix common mistakes - treat anything containing 'official' as official
        result = db.execute(text("""
            UPDATE devices 
            SET device_type = 'official' 
            WHERE is_active = true 
            AND (
                LOWER(device_type) LIKE '%official%' 
                OR LOWER(device_name) LIKE '%official%'
                OR LOWER(device_name) LIKE '%api%'
                OR LOWER(device_name) LIKE '%cloud%'
            )
            AND device_type != 'official'
        """))
        logger.info(f"🔧 Fixed {result.rowcount} devices to official type")
        
        # Fix web devices - treat anything containing 'web', 'qr', 'baileys' as web
        result = db.execute(text("""
            UPDATE devices 
            SET device_type = 'web' 
            WHERE is_active = true 
            AND (
                LOWER(device_type) LIKE '%web%'
                OR LOWER(device_type) LIKE '%qr%'
                OR LOWER(device_type) LIKE '%baileys%'
                OR LOWER(device_name) LIKE '%web%'
                OR LOWER(device_name) LIKE '%qr%'
                OR LOWER(device_name) LIKE '%baileys%'
                OR LOWER(device_name) LIKE '%whatsapp web%'
            )
            AND device_type != 'web'
        """))
        logger.info(f"🔧 Fixed {result.rowcount} devices to web type")
        
        # Any remaining invalid types -> set to web as default
        result = db.execute(text("""
            UPDATE devices 
            SET device_type = 'web' 
            WHERE is_active = true 
            AND device_type NOT IN ('web', 'official', 'mobile', 'desktop')
        """))
        logger.info(f"🔧 Defaulted {result.rowcount} devices to web type")
        
        db.commit()
        logger.info("✅ Device type fixes completed")
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error fixing device types: {e}")
        raise
    finally:
        db.close()

def add_device_type_constraint():
    """Add proper device_type constraint"""
    db = get_db_session()
    try:
        # Check if constraint already exists
        result = db.execute(text("""
            SELECT conname 
            FROM pg_constraint 
            WHERE conrelid = 'devices'::regclass 
            AND conname = 'check_device_type_valid'
        """))
        
        if result.fetchone():
            logger.info("✅ Device type constraint already exists")
            return
        
        # Add constraint
        db.execute(text("""
            ALTER TABLE devices 
            ADD CONSTRAINT check_device_type_valid 
            CHECK (device_type IN ('web', 'official', 'mobile', 'desktop'))
        """))
        
        db.commit()
        logger.info("✅ Added device type constraint")
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error adding constraint: {e}")
        raise
    finally:
        db.close()

def verify_fixes():
    """Verify all fixes worked"""
    logger.info("🔍 Verifying fixes...")
    check_device_type_distribution()
    
    db = get_db_session()
    try:
        # Verify no official devices in unofficial queries
        result = db.execute(text("""
            SELECT COUNT(*) as count 
            FROM devices 
            WHERE is_active = true 
            AND device_type = 'official'
        """))
        official_count = result.fetchone().count
        
        result = db.execute(text("""
            SELECT COUNT(*) as count 
            FROM devices 
            WHERE is_active = true 
            AND device_type = 'web'
        """))
        web_count = result.fetchone().count
        
        logger.info(f"✅ Verification complete:")
        logger.info(f"  Official devices: {official_count}")
        logger.info(f"  Web devices: {web_count}")
        logger.info(f"  Total active devices: {official_count + web_count}")
        
    finally:
        db.close()

def main():
    """Main cleanup function"""
    logger.info("🚀 Starting device type cleanup...")
    
    try:
        # 1. Check current state
        check_device_type_distribution()
        
        # 2. Fix device types
        fix_device_types()
        
        # 3. Add constraint
        add_device_type_constraint()
        
        # 4. Verify fixes
        verify_fixes()
        
        logger.info("🎉 Device type cleanup completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
