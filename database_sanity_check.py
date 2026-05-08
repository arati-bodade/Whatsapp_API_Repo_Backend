#!/usr/bin/env python3
"""
🔍 Database Sanity Check - Device Listing Issues

One-time check to verify device data integrity and fix any issues.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
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

def check_device_data():
    """Check device data integrity"""
    db = get_db_session()
    try:
        # Check all devices
        result = db.execute(text("""
            SELECT 
                device_id,
                busi_user_id,
                device_name,
                device_type,
                session_status,
                is_active,
                created_at,
                updated_at,
                last_active,
                disconnected_at
            FROM devices 
            ORDER BY created_at DESC
        """))
        
        devices = result.fetchall()
        logger.info(f"📊 Total devices in database: {len(devices)}")
        
        if not devices:
            logger.warning("⚠️ No devices found in database")
            return
        
        # Group by user
        users = {}
        for device in devices:
            user_id = str(device.busi_user_id)
            if user_id not in users:
                users[user_id] = []
            users[user_id].append(device)
        
        logger.info(f"👥 Found devices for {len(users)} users")
        
        # Check each user's devices
        for user_id, user_devices in users.items():
            logger.info(f"\n🔍 User {user_id}:")
            
            web_devices = [d for d in user_devices if d.device_type == 'web']
            official_devices = [d for d in user_devices if d.device_type == 'official']
            
            logger.info(f"  Web devices: {len(web_devices)}")
            logger.info(f"  Official devices: {len(official_devices)}")
            
            # Check web devices
            for device in web_devices:
                logger.info(f"    📱 Web: {device.device_name}")
                logger.info(f"       Status: {device.session_status}")
                logger.info(f"       Active: {device.is_active}")
                logger.info(f"       Created: {device.created_at}")
                logger.info(f"       Last Active: {device.last_active}")
                
                # Check for issues
                issues = []
                if not device.is_active:
                    issues.append("Device is inactive")
                if device.session_status not in ['qr_generated', 'connected', 'logged_out']:
                    issues.append(f"Unexpected status: {device.session_status}")
                if not device.last_active and device.session_status == 'connected':
                    issues.append("Connected device has no last_active timestamp")
                
                if issues:
                    logger.warning(f"       ⚠️ Issues: {', '.join(issues)}")
                else:
                    logger.info(f"       ✅ Device looks good")
            
            # Check official devices
            for device in official_devices:
                logger.info(f"    🏢 Official: {device.device_name}")
                logger.info(f"       Status: {device.session_status}")
                logger.info(f"       Active: {device.is_active}")
                logger.info(f"       Created: {device.created_at}")
                
                # Check for issues
                issues = []
                if not device.is_active:
                    issues.append("Official device is inactive")
                if device.session_status != 'connected':
                    issues.append(f"Official device not connected: {device.session_status}")
                
                if issues:
                    logger.warning(f"       ⚠️ Issues: {', '.join(issues)}")
                else:
                    logger.info(f"       ✅ Device looks good")
        
        # Check for any devices with problematic data
        logger.info(f"\n🔍 Checking for problematic devices...")
        
        # Devices with is_active=False
        result = db.execute(text("""
            SELECT COUNT(*) as count 
            FROM devices 
            WHERE is_active = False
        """))
        inactive_count = result.fetchone().count
        if inactive_count > 0:
            logger.warning(f"⚠️ Found {inactive_count} inactive devices")
            
            # Show inactive devices
            result = db.execute(text("""
                SELECT device_id, device_name, device_type, session_status
                FROM devices 
                WHERE is_active = False
            """))
            for device in result.fetchall():
                logger.warning(f"    Inactive: {device.device_name} ({device.device_type}) - {device.session_status}")
        
        # Devices with unexpected statuses
        result = db.execute(text("""
            SELECT COUNT(*) as count 
            FROM devices 
            WHERE session_status NOT IN ('qr_generated', 'connected', 'logged_out', 'disconnected')
        """))
        weird_status_count = result.fetchone().count
        if weird_status_count > 0:
            logger.warning(f"⚠️ Found {weird_status_count} devices with unexpected statuses")
            
            # Show devices with weird statuses
            result = db.execute(text("""
                SELECT device_id, device_name, device_type, session_status
                FROM devices 
                WHERE session_status NOT IN ('qr_generated', 'connected', 'logged_out', 'disconnected')
            """))
            for device in result.fetchall():
                logger.warning(f"    Weird status: {device.device_name} ({device.device_type}) - {device.session_status}")
        
        # Check API filtering simulation
        logger.info(f"\n🧪 Simulating API filtering...")
        
        # Simulate unofficial list API
        result = db.execute(text("""
            SELECT COUNT(*) as count 
            FROM devices 
            WHERE busi_user_id = :user_id 
            AND device_type = 'web'
        """), {"user_id": list(users.keys())[0] if users else "00000000-0000-0000-0000-000000000000"})
        
        unofficial_api_count = result.fetchone().count
        logger.info(f"  /api/devices/unofficial/list would return: {unofficial_api_count} web devices")
        
        # Simulate official list API
        result = db.execute(text("""
            SELECT COUNT(*) as count 
            FROM devices 
            WHERE busi_user_id = :user_id 
            AND device_type = 'official'
        """), {"user_id": list(users.keys())[0] if users else "00000000-0000-0000-0000-000000000000"})
        
        official_api_count = result.fetchone().count
        logger.info(f"  /api/devices/official/list would return: {official_api_count} official devices")
        
    except Exception as e:
        logger.error(f"❌ Error checking device data: {e}")
        raise
    finally:
        db.close()

def fix_device_issues():
    """Fix common device issues"""
    db = get_db_session()
    try:
        logger.info("🔧 Attempting to fix device issues...")
        
        # Fix inactive web devices that should be active
        result = db.execute(text("""
            UPDATE devices 
            SET is_active = True 
            WHERE device_type = 'web' 
            AND is_active = False
            AND session_status IN ('qr_generated', 'connected')
        """))
        
        if result.rowcount > 0:
            logger.info(f"✅ Fixed {result.rowcount} inactive web devices")
            db.commit()
        
        # Fix official devices that should be connected
        result = db.execute(text("""
            UPDATE devices 
            SET session_status = 'connected', is_active = True 
            WHERE device_type = 'official' 
            AND (session_status != 'connected' OR is_active = False)
        """))
        
        if result.rowcount > 0:
            logger.info(f"✅ Fixed {result.rowcount} official devices")
            db.commit()
        
        # Fix web devices with weird statuses
        result = db.execute(text("""
            UPDATE devices 
            SET session_status = 'qr_generated' 
            WHERE device_type = 'web' 
            AND session_status NOT IN ('qr_generated', 'connected', 'logged_out', 'disconnected')
        """))
        
        if result.rowcount > 0:
            logger.info(f"✅ Fixed {result.rowcount} web devices with weird statuses")
            db.commit()
        
        logger.info("🎉 Device fixes completed")
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error fixing devices: {e}")
        raise
    finally:
        db.close()

def main():
    """Main sanity check function"""
    logger.info("🚀 Starting Database Sanity Check...")
    
    try:
        # Check current state
        check_device_data()
        
        # Fix issues
        fix_device_issues()
        
        # Re-check after fixes
        logger.info("\n🔍 Re-checking after fixes...")
        check_device_data()
        
        logger.info("🎉 Database Sanity Check completed!")
        
    except Exception as e:
        logger.error(f"❌ Sanity check failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
