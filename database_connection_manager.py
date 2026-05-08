#!/usr/bin/env python3
"""
Database Connection Manager with Auto-Reconnection
Provides robust database connection management with automatic reconnection
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, text, exc
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from functools import wraps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [DB_MANAGER] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseConnectionManager:
    """Manages database connections with auto-reconnection capabilities"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.last_connection_time = None
        self.connection_attempts = 0
        self.max_retry_attempts = 3
        self.retry_delay = 2  # seconds
        self.health_check_interval = 30  # seconds
        self._background_task = None
        self._should_stop = False
        
    def create_engine(self):
        """Create database engine with robust settings"""
        logger.info("Creating database engine...")
        
        engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=2,
            max_overflow=5,
            pool_timeout=60,
            pool_recycle=120,
            pool_pre_ping=True,
            connect_args={
                "connect_timeout": 60,
                "sslmode": "require",
                "application_name": "whatsapp_platform_manager"
            }
        )
        
        logger.info("Database engine created successfully")
        return engine
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            if not self.engine:
                self.engine = self.create_engine()
            
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test, now() as timestamp"))
                row = result.first()
                
                self.last_connection_time = datetime.now()
                self.connection_attempts = 0
                
                logger.info(f"Connection test successful: {row[0]} at {row[1]}")
                return True
                
        except Exception as e:
            self.connection_attempts += 1
            logger.error(f"Connection test failed (attempt {self.connection_attempts}): {e}")
            return False
    
    def ensure_connection(self) -> bool:
        """Ensure database connection is available, reconnect if needed"""
        if self.test_connection():
            return True
        
        # Try to reconnect
        for attempt in range(self.max_retry_attempts):
            logger.info(f"Reconnection attempt {attempt + 1}/{self.max_retry_attempts}")
            
            try:
                # Dispose old engine if exists
                if self.engine:
                    self.engine.dispose()
                
                # Create new engine
                self.engine = self.create_engine()
                
                # Test new connection
                if self.test_connection():
                    logger.info("Reconnection successful")
                    return True
                
            except Exception as e:
                logger.error(f"Reconnection attempt {attempt + 1} failed: {e}")
            
            # Wait before next attempt
            if attempt < self.max_retry_attempts - 1:
                time.sleep(self.retry_delay)
        
        logger.error("All reconnection attempts failed")
        return False
    
    @contextmanager
    def get_connection(self):
        """Get database connection with auto-reconnection"""
        if not self.ensure_connection():
            raise exc.OperationalError("Could not establish database connection")
        
        try:
            with self.engine.connect() as conn:
                yield conn
        except exc.OperationalError as e:
            logger.error(f"Operational error during connection: {e}")
            # Try to reconnect once more
            if self.ensure_connection():
                with self.engine.connect() as conn:
                    yield conn
            else:
                raise e
    
    def execute_query(self, query: str, params: Optional[dict] = None):
        """Execute query with connection management"""
        with self.get_connection() as conn:
            if params:
                result = conn.execute(text(query), params)
            else:
                result = conn.execute(text(query))
            return result
    
    async def start_health_monitor(self):
        """Start background health monitoring"""
        if self._background_task:
            logger.warning("Health monitor already running")
            return
        
        self._should_stop = False
        self._background_task = asyncio.create_task(self._health_monitor_loop())
        logger.info("Health monitor started")
    
    async def stop_health_monitor(self):
        """Stop background health monitoring"""
        self._should_stop = True
        if self._background_task:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass
            self._background_task = None
        logger.info("Health monitor stopped")
    
    async def _health_monitor_loop(self):
        """Background health monitoring loop"""
        logger.info("Health monitoring loop started")
        
        while not self._should_stop:
            try:
                if not self.test_connection():
                    logger.warning("Health check failed, attempting reconnection")
                    self.ensure_connection()
                
                # Wait for next check
                await asyncio.sleep(self.health_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(5)  # Short wait on error
        
        logger.info("Health monitoring loop stopped")
    
    def get_status(self) -> dict:
        """Get connection manager status"""
        return {
            "database_url": self.database_url.split('@')[1] if '@' in self.database_url else 'unknown',
            "last_connection_time": self.last_connection_time.isoformat() if self.last_connection_time else None,
            "connection_attempts": self.connection_attempts,
            "engine_created": self.engine is not None,
            "health_monitor_running": self._background_task is not None and not self._should_stop
        }
    
    def close(self):
        """Close database engine and cleanup"""
        if self.engine:
            self.engine.dispose()
            self.engine = None
        logger.info("Database connection manager closed")

# Global instance
db_manager = None

def get_db_manager(database_url: str = None) -> DatabaseConnectionManager:
    """Get or create database connection manager"""
    global db_manager
    
    if db_manager is None or database_url:
        if not database_url:
            from core.config import settings
            database_url = settings.DATABASE_URL
        
        db_manager = DatabaseConnectionManager(database_url)
    
    return db_manager

# Decorator for automatic database connection management
def with_db_connection(func):
    """Decorator to ensure database connection before function execution"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        manager = get_db_manager()
        if not manager.ensure_connection():
            raise exc.OperationalError("Database connection not available")
        return func(*args, **kwargs)
    return wrapper

async def main():
    """Main function for testing"""
    # Test with external URL
    external_url = "postgresql://whatsapp_platform_mhnw_user:nComdm17QkuwCzuxi2sMjZrIbXXLV8FG@dpg-d7cbd05ckfvc7387lfog-a.oregon-postgres.render.com/whatsapp_platform_mhnw"
    
    manager = get_db_manager(external_url)
    
    print("Testing database connection manager...")
    
    # Test basic connection
    if manager.test_connection():
        print("Initial connection successful")
    else:
        print("Initial connection failed")
        return
    
    # Test query execution
    try:
        result = manager.execute_query("SELECT version() as version, current_database() as db")
        row = result.first()
        print(f"Database: {row[1]}")
        print(f"Version: {row[0][:50]}...")
    except Exception as e:
        print(f"Query execution failed: {e}")
    
    # Start health monitor
    await manager.start_health_monitor()
    
    # Show status
    print("\nManager Status:")
    status = manager.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # Run for a few seconds
    print("\nMonitoring for 10 seconds...")
    await asyncio.sleep(10)
    
    # Stop health monitor
    await manager.stop_health_monitor()
    
    # Close manager
    manager.close()
    print("\nTest completed")

if __name__ == "__main__":
    asyncio.run(main())
