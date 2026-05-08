#!/usr/bin/env python3
"""
Diagnose backend database connection issues
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.config import settings
from db.base import engine
from sqlalchemy import text
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def diagnose_connection():
    """Diagnose database connection issues"""
    logger.info("🔍 BACKEND DATABASE CONNECTION DIAGNOSIS")
    logger.info("=" * 50)
    
    # Check configuration
    logger.info("📋 Configuration Check:")
    logger.info(f"  DATABASE_URL: {settings.DATABASE_URL}")
    logger.info(f"  APP_NAME: {settings.APP_NAME}")
    logger.info(f"  DEBUG: {settings.DEBUG}")
    
    # Check if .env file exists
    env_file_path = os.path.join(os.path.dirname(__file__), '.env')
    logger.info(f"  .env file exists: {os.path.exists(env_file_path)}")
    
    if os.path.exists(env_file_path):
        try:
            with open(env_file_path, 'r') as f:
                env_content = f.read()
                logger.info("  .env file content preview:")
                for line in env_content.split('\n')[:5]:  # Show first 5 lines
                    if line.strip() and not line.startswith('#'):
                        logger.info(f"    {line}")
        except Exception as e:
            logger.error(f"  Error reading .env file: {e}")
    
    logger.info("")
    logger.info("🔗 Testing Database Connection:")
    
    try:
        # Test connection using the same engine as the backend
        with engine.connect() as conn:
            # Basic connection test
            result = conn.execute(text("SELECT 1 as test"))
            test_value = result.scalar()
            logger.info(f"  ✅ Basic connection test: {test_value}")
            
            # Check database version
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"  ✅ Database version: {version[:50]}...")
            
            # Check current database
            result = conn.execute(text("SELECT current_database()"))
            current_db = result.scalar()
            logger.info(f"  ✅ Current database: {current_db}")
            
            # Check current user
            result = conn.execute(text("SELECT current_user"))
            current_user = result.scalar()
            logger.info(f"  ✅ Current user: {current_user}")
            
            # Test table access
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            table_count = result.scalar()
            logger.info(f"  ✅ Table count: {table_count}")
            
            # Test specific table access
            result = conn.execute(text("SELECT COUNT(*) FROM businesses"))
            business_count = result.scalar()
            logger.info(f"  ✅ Businesses table accessible: {business_count} records")
            
        logger.info("")
        logger.info("🎉 DATABASE CONNECTION IS WORKING!")
        logger.info("✅ Backend should be able to connect to the database")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        
        # Provide specific troubleshooting steps
        logger.info("")
        logger.info("🔧 TROUBLESHOOTING STEPS:")
        logger.info("1. Check if .env file exists and contains correct DATABASE_URL")
        logger.info("2. Verify database credentials are correct")
        logger.info("3. Check network connectivity to database host")
        logger.info("4. Ensure database is running and accessible")
        logger.info("5. Check if SSL connection is required")
        
        return False

def test_backend_imports():
    """Test if backend can import database modules"""
    logger.info("")
    logger.info("📦 Testing Backend Imports:")
    
    try:
        from db.session import get_db
        logger.info("  ✅ db.session imported successfully")
        
        # Test specific model imports instead of *
        from models.busi_user import BusiUser
        from models.device import Device
        from models.message import Message
        logger.info("  ✅ Core models imported successfully")
        
        # Test API imports
        from api.auth import router as auth_router
        logger.info("  ✅ API modules imported successfully")
        
        return True
    except Exception as e:
        logger.error(f"  ❌ Import error: {e}")
        return False

def main():
    """Main diagnosis function"""
    success = diagnose_connection()
    imports_ok = test_backend_imports()
    
    logger.info("")
    logger.info("📊 DIAGNOSIS SUMMARY:")
    if success and imports_ok:
        logger.info("✅ Everything looks good - backend should connect successfully")
        logger.info("💡 If backend still can't connect, check:")
        logger.info("   - Backend startup logs for specific error messages")
        logger.info("   - Environment variables in runtime environment")
        logger.info("   - Database connection pool settings")
    else:
        logger.info("❌ Issues found - please address the problems above")

if __name__ == "__main__":
    main()
