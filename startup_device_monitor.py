#!/usr/bin/env python3
"""
🚀 STARTUP DEVICE MONITOR

This script initializes and starts the device monitoring service
when the backend application starts up.

It ensures continuous monitoring of device connections
and automatic recovery when connections drop.

Usage:
    python startup_device_monitor.py

Or import and call from your main application:
    from startup_device_monitor import initialize_device_monitoring
    initialize_device_monitoring()
"""

import logging
import atexit
import time
from db.session import SessionLocal
from services.device_monitor_service import start_device_monitoring, stop_device_monitoring

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def initialize_device_monitoring():
    """
    Initialize the device monitoring service with proper cleanup
    """
    try:
        logger.info("🚀 Initializing device monitoring service...")
        
        # Create session factory for the monitor service
        def session_factory():
            return SessionLocal()
        
        # Import and configure the monitor service
        from services.device_monitor_service import device_monitor_service
        device_monitor_service.db_session_factory = session_factory
        
        # Start the monitoring service
        start_device_monitoring()
        
        # Register cleanup function to ensure graceful shutdown
        atexit.register(cleanup_device_monitoring)
        
        logger.info("✅ Device monitoring service initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize device monitoring: {e}")
        return False

def cleanup_device_monitoring():
    """
    Cleanup function to stop monitoring service gracefully
    """
    try:
        logger.info("🛑 Cleaning up device monitoring service...")
        stop_device_monitoring()
        logger.info("✅ Device monitoring service stopped gracefully")
    except Exception as e:
        logger.error(f"❌ Error during cleanup: {e}")

def test_monitoring_service():
    """
    Test function to verify monitoring service is working
    """
    try:
        from services.device_monitor_service import device_monitor_service
        
        # Test force sync
        logger.info("🧪 Testing monitoring service...")
        with SessionLocal() as db:
            result = device_monitor_service.force_sync_all_devices()
            
        if result.get("success"):
            logger.info(f"✅ Monitoring service test passed: {result}")
            return True
        else:
            logger.error(f"❌ Monitoring service test failed: {result}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Monitoring service test error: {e}")
        return False

if __name__ == "__main__":
    """
    Standalone execution for testing
    """
    print("🔧 Device Monitor Startup Script")
    print("=" * 50)
    
    # Initialize monitoring
    success = initialize_device_monitoring()
    
    if success:
        print("✅ Monitoring service started successfully!")
        
        # Test the service
        print("\n🧪 Running test...")
        test_result = test_monitoring_service()
        
        if test_result:
            print("✅ All tests passed!")
        else:
            print("❌ Tests failed!")
            
        print("\n📡 Monitoring is now running in the background.")
        print("   Press Ctrl+C to stop...")
        
        try:
            # Keep the script running
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            print("\n🛑 Stopping monitoring...")
            cleanup_device_monitoring()
            print("✅ Done!")
    else:
        print("❌ Failed to start monitoring service!")
        exit(1)
